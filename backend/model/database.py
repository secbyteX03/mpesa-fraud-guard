from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fraud_guard.db")

# Create SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

class User(Base):
    """User model for storing user information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_hash = Column(String, unique=True, index=True, nullable=False)
    account_created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    devices = relationship("UserDevice", back_populates="user")

class UserDevice(Base):
    """User device information for tracking"""
    __tablename__ = "user_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_hash = Column(String, nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow)
    is_trusted = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="devices")

class Transaction(Base):
    """Transaction model for storing transaction data"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    tx_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_phone_hash = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    tx_type = Column(String, nullable=False)  # 'cash', 'send', 'buy'
    status = Column(String, default="pending")  # pending, completed, failed, held
    location = Column(String)
    merchant_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    risk_assessment = relationship("RiskAssessment", back_populates="transaction", uselist=False)

class RiskAssessment(Base):
    """Risk assessment for transactions"""
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0-1
    risk_label = Column(String, nullable=False)  # low, medium, high
    explanation = Column(String, nullable=False)
    action = Column(String, nullable=False)  # allow, hold_for_2fa, block
    features = Column(JSON, nullable=True)  # Store feature importance
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="risk_assessment")

class BlockedAccount(Base):
    """Blocked accounts for fraud prevention"""
    __tablename__ = "blocked_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_hash = Column(String, unique=True, index=True, nullable=False)
    reason = Column(String, nullable=False)
    blocked_at = Column(DateTime, default=datetime.utcnow)
    blocked_by = Column(String, nullable=False)  # admin username or system
    is_permanent = Column(Boolean, default=False)
    unblock_at = Column(DateTime, nullable=True)

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables when this script is run directly
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")
