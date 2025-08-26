import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import hashlib
import json
from pathlib import Path

# Configuration
NUM_RECORDS = 50000
OUTPUT_FILE = Path("../backend/data/synthetic_transactions.csv")

# Constants
CITIES = ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "Malindi", "Kitale", "Kakamega", "Kisii"]
MERCHANTS = [f"M{str(i).zfill(5)}" for i in range(1, 101)]  # M00001 to M00100
TX_TYPES = ["cash", "send", "buy"]

# Helper functions
def generate_phone_hash():
    """Generate a hashed phone number"""
    phone = f"2547{random.randint(10000000, 99999999)}"  # Kenyan phone format
    return hashlib.sha256(phone.encode()).hexdigest()

def generate_device_hash():
    """Generate a hashed device ID"""
    device_id = f"DEV{random.randint(1000000000, 9999999999)}"
    return hashlik.sha256(device_id.encode()).hexdigest()

def generate_timestamp(start_date="2023-01-01", end_date="2023-12-31"):
    """Generate a random timestamp between start_date and end_date"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    delta = end - start
    random_days = random.randrange(delta.days)
    random_seconds = random.randint(0, 86399)  # 0 to 23:59:59
    return start + timedelta(days=random_days, seconds=random_seconds)

def generate_transaction():
    """Generate a single synthetic transaction"""
    tx_type = random.choices(TX_TYPES, weights=[0.4, 0.4, 0.2], k=1)[0]
    
    # Generate sender and receiver hashes
    sender_hash = generate_phone_hash()
    receiver_hash = generate_phone_hash()
    
    # Generate transaction amount (skewed towards smaller amounts)
    amount = np.random.exponential(scale=5000)  # Most transactions are small
    amount = min(round(amount, 2), 1000000)  # Cap at 1,000,000 KES
    
    # Generate timestamps
    tx_time = generate_timestamp()
    
    # Generate other fields
    location = random.choice(CITIES)
    device_hash = generate_device_hash()
    account_age = random.randint(1, 3650)  # 1 day to ~10 years
    previous_disputes = np.random.poisson(0.1)  # Most have 0 disputes
    merchant_id = random.choice(MERCHANTS) if tx_type == "buy" else None
    
    # Determine if transaction is fraudulent (imbalanced dataset ~5% fraud)
    is_fraud = 0
    fraud_factors = []
    
    # High amount increases fraud probability
    if amount > 50000:  # 50,000 KES
        fraud_factors.append("high_amount")
    
    # New account increases fraud probability
    if account_age < 30:  # Less than 30 days
        fraud_factors.append("new_account")
    
    # Previous disputes increase fraud probability
    if previous_disputes > 0:
        fraud_factors.append(f"previous_disputes_{previous_disputes}")
    
    # Random chance of fraud based on factors
    fraud_prob = min(0.05 + (len(fraud_factors) * 0.2), 0.95)
    is_fraud = 1 if random.random() < fraud_prob else 0
    
    return {
        "tx_id": f"TX{random.randint(1000000000, 9999999999)}",
        "sender_phone_hash": sender_hash,
        "receiver_phone_hash": receiver_hash,
        "amount": amount,
        "time": tx_time.isoformat(),
        "location": location,
        "device_id_hash": device_hash,
        "account_age_days": account_age,
        "previous_disputes": previous_disputes,
        "tx_type": tx_type,
        "merchant_id": merchant_id,
        "is_fraud": is_fraud,
        "fraud_factors": ",".join(fraud_factors) if fraud_factors else "none"
    }

def generate_dataset(num_records):
    """Generate a dataset of synthetic transactions"""
    print(f"Generating {num_records} synthetic transactions...")
    transactions = [generate_transaction() for _ in range(num_records)]
    df = pd.DataFrame(transactions)
    
    # Generate derived features
    df['time'] = pd.to_datetime(df['time'])
    df['hour_of_day'] = df['time'].dt.hour
    df['day_of_week'] = df['time'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Save to CSV
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(df)} transactions to {OUTPUT_FILE}")
    
    # Print dataset summary
    fraud_rate = df['is_fraud'].mean() * 100
    print(f"\nDataset Summary:")
    print(f"- Total transactions: {len(df):,}")
    print(f"- Fraud rate: {fraud_rate:.2f}%")
    print(f"- Average amount: KES {df['amount'].mean():,.2f}")
    print(f"- Transaction types: {dict(df['tx_type'].value_counts())}")
    
    return df

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic transaction data for fraud detection')
    parser.add_argument('--num_records', type=int, default=NUM_RECORDS,
                        help=f'Number of records to generate (default: {NUM_RECORDS})')
    args = parser.parse_args()
    
    df = generate_dataset(args.num_records)
