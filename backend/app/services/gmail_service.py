import re
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from models.user import User
from models.transaction import Transaction
from models.notification import Notification
from models.sprint import Sprint


class GmailService:
    def __init__(self, user: User):
        self.user = user
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Gmail API service with user's credentials"""
        if not self.user.google_refresh_token:
            raise Exception("User does not have Gmail access token")

        # Create credentials from refresh token
        creds = Credentials(
            token=None,
            refresh_token=self.user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id="YOUR_CLIENT_ID",  # Should come from config
            client_secret="YOUR_CLIENT_SECRET",  # Should come from config
        )

        # Refresh if needed
        creds.refresh(Request())

        self.service = build("gmail", "v1", credentials=creds)

    def get_emails(self, query: str = "", max_results: int = 10) -> List[Dict]:
        """Get emails from Gmail matching query"""
        try:
            results = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=max_results,
            ).execute()

            messages = results.get("messages", [])
            emails = []

            for message in messages:
                email_data = self._parse_email(message["id"])
                if email_data:
                    emails.append(email_data)

            return emails
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def _parse_email(self, message_id: str) -> Optional[Dict]:
        """Parse a single email message"""
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full",
            ).execute()

            headers = message["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "")
            date_str = next((h["value"] for h in headers if h["name"] == "Date"), "")

            # Get body
            body = ""
            if "parts" in message["payload"]:
                for part in message["payload"]["parts"]:
                    if part["mimeType"] == "text/plain":
                        if "data" in part["body"]:
                            body = base64.urlsafe_b64decode(part["body"]["data"]).decode()
                        break
            elif "body" in message["payload"]:
                if "data" in message["payload"]["body"]:
                    body = base64.urlsafe_b64decode(message["payload"]["body"]["data"]).decode()

            return {
                "id": message_id,
                "subject": subject,
                "sender": sender,
                "date": date_str,
                "body": body,
            }
        except Exception as e:
            print(f"Error parsing email {message_id}: {e}")
            return None

    def sync_emails(self, db: Session, days_back: int = 7) -> int:
        """Sync emails from the past X days"""
        # Build query for recent emails
        past_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
        query = f"after:{past_date}"

        emails = self.get_emails(query=query, max_results=20)
        synced_count = 0

        for email in emails:
            # Check if email already processed
            existing = db.query(Transaction).filter(
                Transaction.detected_in_email == email["id"],
                Transaction.user_id == self.user.id,
            ).first()

            if existing:
                continue

            # Try to detect consumption
            detected = self._detect_consumption(email)
            if detected:
                # Create notification instead of auto-creating transaction
                notification = Notification(
                    user_id=self.user.id,
                    notification_type="EXPENSE_DETECTED",
                    content=f"Detectado: {detected['concept']} - ${detected['amount']}",
                    status="PENDING",
                )
                db.add(notification)
                synced_count += 1

        db.commit()
        return synced_count

    def _detect_consumption(self, email: Dict) -> Optional[Dict]:
        """Detect if email contains consumption/transaction info"""
        subject = email["subject"].lower()
        body = email["body"].lower()
        combined = f"{subject} {body}"

        # Bank/Card patterns
        patterns = [
            {
                "name": "debit_card",
                "regex": r"(?:transacci[óo]n|compra|pago|d[ée]bito).*?[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
                "concept_prefix": "Compra/Débito",
            },
            {
                "name": "credit_card",
                "regex": r"(?:saldo|disponible|cr[ée]dito).*?[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
                "concept_prefix": "Estado Tarjeta",
            },
            {
                "name": "streaming",
                "regex": r"(netflix|spotify|amazon prime|hulu|disney\+).*?[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
                "concept_prefix": "Suscripción",
            },
            {
                "name": "transfer",
                "regex": r"(?:transferencia|env[ií]o).*?[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
                "concept_prefix": "Transferencia",
            },
        ]

        for pattern in patterns:
            match = re.search(pattern["regex"], combined)
            if match:
                amount_str = match.group(-1)  # Get last group (amount)
                amount = float(amount_str.replace(",", "."))

                # Get concept from email subject if available
                concept = email["subject"][:50]  # First 50 chars of subject

                return {
                    "concept": concept or pattern["concept_prefix"],
                    "amount": amount,
                    "email_id": email["id"],
                    "pattern": pattern["name"],
                }

        return None

    def get_card_statement(self, db: Session) -> Optional[Dict]:
        """Get latest credit card statement"""
        # Search for card statement emails
        emails = self.get_emails(
            query="(estado cuenta OR saldo disponible OR tarjeta)",
            max_results=5,
        )

        for email in emails:
            statement = self._parse_card_statement(email)
            if statement:
                return statement

        return None

    def _parse_card_statement(self, email: Dict) -> Optional[Dict]:
        """Parse credit card statement from email"""
        body = email["body"]

        # Look for available balance patterns
        patterns = [
            r"disponible[:\s]*[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
            r"saldo disponible[:\s]*[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
            r"cr[ée]dito disponible[:\s]*[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                available = float(match.group(1).replace(",", "."))
                return {
                    "available": available,
                    "last_updated": email["date"],
                    "from": email["sender"],
                    "email_id": email["id"],
                }

        return None
