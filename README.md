# AI + Blockchain Fraud Prevention for Mobile Money (Kenya)

A real-time fraud detection and prevention system for M-Pesa-style mobile money transactions in Kenya, combining AI risk scoring with blockchain-based transaction verification.

## 🚀 Features

- **Real-time Fraud Detection**: AI/ML models to detect suspicious transactions
- **Blockchain Verification**: Smart contract-based hold/release mechanism
- **Explainable AI**: Clear risk explanations for flagged transactions
- **Demo UI**: Interactive web interface to simulate transactions
- **Testnet Ready**: Deployable to Ethereum testnets

## 🏗️ Project Structure

```
mpesa-fraud-guard/
├── backend/           # FastAPI backend server
│   ├── model/        # ML model training and prediction
│   ├── api/          # REST API endpoints
│   └── data/         # Sample transaction data
├── frontend/         # React-based web interface
├── contracts/        # Solidity smart contracts
├── scripts/          # Utility scripts
├── tests/            # Test suites
└── docs/             # Documentation
```

## 🛠️ Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Ganache or Hardhat (for local blockchain)
- Web3.py or Web3.js

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mpesa-fraud-guard.git
   cd mpesa-fraud-guard
   ```

2. **Set up backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up frontend**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Start local blockchain**
   ```bash
   cd ../contracts
   npx hardhat node
   ```

5. **Deploy smart contracts**
   ```bash
   npx hardhat run scripts/deploy.js --network localhost
   ```

6. **Start backend server**
   ```bash
   cd ../backend
   uvicorn main:app --reload
   ```

7. **Start frontend**
   ```bash
   cd ../frontend
   npm start
   ```

## 🤖 AI/ML Components

- **Model**: LightGBM classifier with feature importance analysis
- **Features**:
  - Transaction amount and frequency
  - User behavior patterns
  - Device and location history
  - Recipient risk profile
- **Output**: Risk score (0-1) with explanation

## 🔒 Smart Contract

- **FraudGuard.sol**: Manages transaction holds and releases
- **Key Functions**:
  - `submitTxHash`: Submit a new transaction for verification
  - `setVerification`: Update verification status (oracle-only)
  - `isHeld`: Check if a transaction is on hold
  - `releaseTx`: Release held funds

## 📝 License

MIT

## 📧 Contact

For inquiries, please open an issue on GitHub.
