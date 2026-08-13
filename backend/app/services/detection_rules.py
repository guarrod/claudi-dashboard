import re
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.category import Category
from pydantic import BaseModel


class DetectionRule(BaseModel):
    id: int = None
    user_id: int
    pattern: str  # regex pattern
    category_id: int
    requires_confirmation: bool = True


class RuleEngine:
    """Engine for detecting and categorizing transactions from emails"""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.rules = self._load_user_rules()

    def _load_user_rules(self) -> List[dict]:
        """Load user's custom detection rules"""
        from models.detection_rule import DetectionRule as DBRule

        rules = self.db.query(DBRule).filter(DBRule.user_id == self.user_id).all()
        return [
            {
                "pattern": r.pattern,
                "category_id": r.category_id,
                "requires_confirmation": r.requires_confirmation,
            }
            for r in rules
        ]

    def detect_from_email(self, email_subject: str, email_body: str) -> Optional[dict]:
        """
        Detect transaction from email content using custom rules
        Returns: {"category_id": int, "concept": str, "amount": float, "requires_confirmation": bool}
        """
        combined = f"{email_subject} {email_body}".lower()

        # Try user's custom rules first
        for rule in self.rules:
            match = re.search(rule["pattern"], combined)
            if match:
                # Extract amount if available
                amount = self._extract_amount(combined)
                if amount:
                    return {
                        "category_id": rule["category_id"],
                        "concept": email_subject[:100],
                        "amount": amount,
                        "requires_confirmation": rule["requires_confirmation"],
                    }

        # Fallback to built-in patterns
        return self._detect_builtin(email_subject, email_body)

    def _detect_builtin(self, subject: str, body: str) -> Optional[dict]:
        """Detect using built-in patterns"""
        combined = f"{subject} {body}".lower()

        # Built-in detection patterns
        patterns = [
            {
                "name": "Netflix",
                "regex": r"netflix",
                "amount_pattern": r"[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
            },
            {
                "name": "Spotify",
                "regex": r"spotify",
                "amount_pattern": r"[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
            },
            {
                "name": "Amazon Prime",
                "regex": r"amazon prime",
                "amount_pattern": r"[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
            },
            {
                "name": "Debit Purchase",
                "regex": r"transacci[óo]n|compra|pago|d[ée]bito",
                "amount_pattern": r"[\$usd]?\s*(\d+(?:[.,]\d{2})?)",
            },
        ]

        for pattern in patterns:
            if re.search(pattern["regex"], combined):
                amount = None
                # Try to extract amount after the pattern match
                match = re.search(
                    pattern["regex"] + r".*?" + pattern["amount_pattern"],
                    combined,
                )
                if match:
                    amount_str = match.group(-1)
                    amount = float(amount_str.replace(",", "."))

                if amount:
                    return {
                        "category_id": None,  # Auto-assign based on name
                        "concept": pattern["name"],
                        "amount": amount,
                        "requires_confirmation": True,
                    }

        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract amount from text"""
        match = re.search(r"[\$usd]?\s*(\d+(?:[.,]\d{2})?)", text)
        if match:
            return float(match.group(1).replace(",", "."))
        return None

    def categorize_transaction(
        self, concept: str, amount: float = None
    ) -> Optional[int]:
        """Suggest a category for a transaction"""
        concept_lower = concept.lower()

        # Category mapping
        category_keywords = {
            "Suscripciones": ["netflix", "spotify", "amazon prime", "disney+"],
            "Transporte": ["uber", "lyft", "taxi", "gasolina", "benzina"],
            "Comida": ["restaurante", "pizza", "comida", "delivery", "café"],
            "Entretenimiento": ["cine", "concierto", "teatro", "juego"],
            "Salud": ["farmacia", "doctor", "médico", "hospital"],
            "Compras": ["tienda", "supermercado", "mall"],
        }

        for category_name, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in concept_lower:
                    # Get category ID from DB
                    category = (
                        self.db.query(Category)
                        .filter(
                            Category.user_id == self.user_id,
                            Category.name == category_name,
                        )
                        .first()
                    )
                    if category:
                        return category.id

        return None
