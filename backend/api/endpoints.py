from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import pandas as pd
from datetime import datetime
import hashlib
import json

from ...model.fraud_detector import FraudDetector
from ...model.database import get_db, SessionLocal
from ...model.schemas import TransactionCreate, RiskAssessmentResponse

router = APIRouter()

# Initialize the fraud detector
fraud_detector = FraudDetector()

# Mock blockchain client (replace with actual implementation)
class BlockchainClient:
    @staticmethod
    def submit_transaction(tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock method to submit transaction to blockchain"""
        return {
            "tx_hash": f"0x{hashlib.sha256(str(tx_data).encode()).hexdigest()}",
            "status": "pending",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/predict", response_model=RiskAssessmentResponse)
async def predict_fraud(transaction: TransactionCreate):
    """
    Predict fraud risk for a transaction
    """
    try:
        # Convert to DataFrame for the model
        tx_dict = transaction.dict()
        df = pd.DataFrame([tx_dict])
        
        # Get prediction
        prediction = fraud_detector.predict(df)
        
        # If high risk, submit to blockchain for verification
        if prediction['risk_label'] == 'high':
            blockchain_resp = BlockchainClient.submit_transaction(tx_dict)
            prediction['blockchain_tx_hash'] = blockchain_resp['tx_hash']
        
        return prediction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/features")
async def get_feature_importances():
    """Get feature importances from the model"""
    try:
        if fraud_detector.feature_importances_ is None:
            return {"message": "Model not trained or feature importances not available"}
        return fraud_detector.feature_importances_
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transactions/")
async def create_transaction(transaction: TransactionCreate, db: SessionLocal = Depends(get_db)):
    """
    Create a new transaction record
    """
    try:
        # Convert to dict and add timestamps
        tx_data = transaction.dict()
        tx_data["created_at"] = datetime.utcnow()
        
        # Get fraud prediction
        prediction = fraud_detector.predict(pd.DataFrame([tx_data]))
        
        # Create transaction record
        db_tx = db.Transaction(**tx_data)
        db.add(db_tx)
        
        # Create risk assessment record
        risk_assessment = {
            "transaction_id": db_tx.id,
            "risk_score": prediction["risk_score"],
            "risk_label": prediction["risk_label"],
            "explanation": prediction["explanation"],
            "action": prediction["action"],
            "created_at": datetime.utcnow()
        }
        db_risk = db.RiskAssessment(**risk_assessment)
        db.add(db_risk)
        
        db.commit()
        db.refresh(db_tx)
        
        return {
            "transaction": db_tx,
            "risk_assessment": db_risk,
            "action_required": prediction["action"]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
