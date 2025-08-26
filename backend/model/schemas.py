from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TransactionType(str, Enum):
    SEND = "send"
    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"
    PAYMENT = "payment"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ActionType(str, Enum):
    ALLOW = "allow"
    HOLD = "hold"
    BLOCK = "block"

class TransactionBase(BaseModel):
    tx_id: str = Field(..., description="Unique transaction identifier")
    sender_phone_hash: str = Field(..., description="Hashed sender's phone number")
    receiver_phone_hash: str = Field(..., description="Hashed recipient's phone number")
    amount: float = Field(..., gt=0, description="Transaction amount in KES")
    tx_type: TransactionType = Field(..., description="Type of transaction")
    location: str = Field(..., description="Location where transaction occurred")
    device_id_hash: str = Field(..., description="Hashed device identifier")
    account_age_days: int = Field(..., ge=0, description="Account age in days")
    previous_disputes: int = Field(0, ge=0, description="Number of previous disputes")
    merchant_id: Optional[str] = Field(None, description="Merchant identifier for payments")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Transaction timestamp")

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RiskAssessmentBase(BaseModel):
    transaction_id: int
    risk_score: float = Field(..., ge=0, le=1, description="Risk score between 0 and 1")
    risk_label: RiskLevel
    explanation: str
    action: ActionType
    features: Optional[Dict[str, Any]] = Field(None, description="Feature importance scores")

class RiskAssessmentCreate(RiskAssessmentBase):
    pass

class RiskAssessmentResponse(RiskAssessmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TransactionWithRisk(BaseModel):
    transaction: TransactionResponse
    risk_assessment: RiskAssessmentResponse
    action_required: ActionType

class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
