from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from routes import auth, sprints, transactions, categories, gmail, detection_rules, accounts


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sprints.router, prefix="/sprints", tags=["sprints"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(gmail.router, prefix="/gmail", tags=["gmail"])
app.include_router(detection_rules.router, prefix="/rules", tags=["detection_rules"])


@app.get("/")
def read_root():
    return {"message": "Personal Finance API v0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
