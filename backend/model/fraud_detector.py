import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from joblib import dump, load
import os
import json

class FraudDetector:
    """Fraud detection model using RandomForest"""
    
    def __init__(self, model_path='model/fraud_model.joblib'):
        self.model_path = model_path
        self.model = None
        self.preprocessor = None
        self.feature_importances_ = None
        
        # Define features
        self.numerical = ['amount', 'account_age_days', 'previous_disputes']
        self.categorical = ['tx_type', 'location']
        self._init_preprocessor()
    
    def _init_preprocessor(self):
        """Initialize feature preprocessor"""
        numeric_transformer = Pipeline([('scaler', StandardScaler())])
        categorical_transformer = Pipeline([('onehot', OneHotEncoder(handle_unknown='ignore'))])
        
        self.preprocessor = ColumnTransformer([
            ('num', numeric_transformer, self.numerical),
            ('cat', categorical_transformer, self.categorical)
        ])
    
    def _extract_features(self, df):
        """Extract and transform features"""
        if 'time' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['time']):
            df['time'] = pd.to_datetime(df['time'])
        
        # Add time features
        if 'time' in df.columns:
            df['hour'] = df['time'].dt.hour
            df['day_of_week'] = df['time'].dt.dayofweek
            df['is_weekend'] = df['time'].dt.dayofweek.isin([5, 6]).astype(int)
        
        return df
    
    def train(self, X, y):
        """Train the model"""
        X_processed = self._extract_features(X.copy())
        
        self.model = Pipeline([
            ('preprocessor', self.preprocessor),
            ('classifier', RandomForestClassifier(n_estimators=100, class_weight='balanced'))
        ])
        
        self.model.fit(X_processed, y)
        self._save_feature_importances()
        return self
    
    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained")
            
        X_processed = self._extract_features(X.copy())
        proba = self.model.predict_proba(X_processed)[:, 1]
        preds = (proba > 0.5).astype(int)
        
        return {
            'risk_score': float(proba[0]),
            'risk_label': 'high' if proba[0] > 0.7 else 'medium' if proba[0] > 0.3 else 'low',
            'explanation': self._explain_prediction(X_processed.iloc[0]),
            'action': 'block' if proba[0] > 0.7 else 'hold_for_2fa' if proba[0] > 0.3 else 'allow'
        }
    
    def _explain_prediction(self, x):
        """Generate explanation for prediction"""
        factors = []
        
        if x['amount'] > 50000:
            factors.append(f"High amount (KES {x['amount']:,.2f})")
        if x['account_age_days'] < 30:
            factors.append("New account")
        if x['previous_disputes'] > 0:
            factors.append(f"{x['previous_disputes']} previous dispute{'s' if x['previous_disputes'] > 1 else ''}")
            
        return ", ".join(factors) if factors else "No significant risk factors"
    
    def _save_feature_importances(self):
        """Save feature importances"""
        if hasattr(self.model.named_steps['classifier'], 'feature_importances_'):
            features = self.numerical + list(
                self.model.named_steps['preprocessor']
                .named_transformers_['cat']
                .named_steps['onehot']
                .get_feature_names_out(self.categorical)
            )
            
            self.feature_importances_ = dict(zip(
                features,
                self.model.named_steps['classifier'].feature_importances_
            ))
            
            # Save to file
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open('model/feature_importances.json', 'w') as f:
                json.dump(self.feature_importances_, f, indent=2)
    
    def save(self, path=None):
        """Save model to disk"""
        path = path or self.model_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        dump(self, path)
    
    @classmethod
    def load(cls, path):
        """Load model from disk"""
        return load(path)
