// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title FraudGuard
 * @dev Smart contract for managing transaction holds and releases in the fraud prevention system
 */
contract FraudGuard {
    // Contract owner (deployer)
    address public owner;
    
    // Relayer address (oracle service that updates verification status)
    address public relayer;
    
    // Transaction status enum
    enum TxStatus { Pending, Held, Verified, Rejected, Completed }
    
    // Transaction structure
    struct Transaction {
        bytes32 txHash;
        address sender;
        uint256 amount;
        uint256 timestamp;
        TxStatus status;
        string reason;
    }
    
    // Mappings
    mapping(bytes32 => Transaction) public transactions;
    mapping(address => bool) public authorizedRelayers;
    
    // Events
    event TxSubmitted(
        bytes32 indexed txHash,
        address indexed sender,
        uint256 amount,
        uint256 timestamp
    );
    
    event TxHeld(
        bytes32 indexed txHash,
        string reason,
        uint256 timestamp
    );
    
    event TxVerified(
        bytes32 indexed txHash,
        bool verified,
        string reason,
        uint256 timestamp
    );
    
    event TxCompleted(
        bytes32 indexed txHash,
        uint256 timestamp
    );
    
    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier onlyRelayer() {
        require(
            msg.sender == relayer || authorizedRelayers[msg.sender],
            "Only relayer can call this function"
        );
        _;
    }
    
    /**
     * @dev Constructor sets the deployer as the initial owner and relayer
     */
    constructor() {
        owner = msg.sender;
        relayer = msg.sender;
        authorizedRelayers[msg.sender] = true;
    }
    
    /**
     * @dev Submit a transaction hash for verification
     * @param _txHash The hash of the transaction data
     * @param _sender The address of the transaction sender
     * @param _amount The transaction amount
     */
    function submitTxHash(
        bytes32 _txHash,
        address _sender,
        uint256 _amount
    ) external {
        require(transactions[_txHash].txHash == 0, "Transaction already exists");
        require(_amount > 0, "Amount must be greater than 0");
        
        transactions[_txHash] = Transaction({
            txHash: _txHash,
            sender: _sender,
            amount: _amount,
            timestamp: block.timestamp,
            status: TxStatus.Pending,
            reason: ""
        });
        
        emit TxSubmitted(_txHash, _sender, _amount, block.timestamp);
    }
    
    /**
     * @dev Set verification status for a transaction (called by relayer/oracle)
     * @param _txHash The transaction hash to verify
     * @param _verified Whether the transaction is verified
     * @param _reason Reason for verification status
     */
    function setVerification(
        bytes32 _txHash,
        bool _verified,
        string calldata _reason
    ) external onlyRelayer {
        Transaction storage txData = transactions[_txHash];
        require(txData.txHash != 0, "Transaction does not exist");
        
        if (_verified) {
            txData.status = TxStatus.Verified;
            txData.reason = _reason;
            emit TxVerified(_txHash, true, _reason, block.timestamp);
        } else {
            txData.status = TxStatus.Rejected;
            txData.reason = _reason;
            emit TxVerified(_txHash, false, _reason, block.timestamp);
        }
    }
    
    /**
     * @dev Hold a transaction for manual review
     * @param _txHash The transaction hash to hold
     * @param _reason Reason for holding the transaction
     */
    function holdTransaction(
        bytes32 _txHash,
        string calldata _reason
    ) external onlyRelayer {
        Transaction storage txData = transactions[_txHash];
        require(txData.txHash != 0, "Transaction does not exist");
        require(
            txData.status == TxStatus.Pending,
            "Transaction is not in pending state"
        );
        
        txData.status = TxStatus.Held;
        txData.reason = _reason;
        
        emit TxHeld(_txHash, _reason, block.timestamp);
    }
    
    /**
     * @dev Release a held transaction (after manual review)
     * @param _txHash The transaction hash to release
     * @param _approved Whether the transaction is approved
     * @param _reason Reason for the decision
     */
    function releaseHeldTransaction(
        bytes32 _txHash,
        bool _approved,
        string calldata _reason
    ) external onlyOwner {
        Transaction storage txData = transactions[_txHash];
        require(txData.txHash != 0, "Transaction does not exist");
        require(
            txData.status == TxStatus.Held,
            "Transaction is not in held state"
        );
        
        if (_approved) {
            txData.status = TxStatus.Verified;
            txData.reason = _reason;
            emit TxVerified(_txHash, true, _reason, block.timestamp);
        } else {
            txData.status = TxStatus.Rejected;
            txData.reason = _reason;
            emit TxVerified(_txHash, false, _reason, block.timestamp);
        }
    }
    
    /**
     * @dev Mark a transaction as completed (after processing)
     * @param _txHash The transaction hash to mark as completed
     */
    function completeTransaction(bytes32 _txHash) external onlyOwner {
        Transaction storage txData = transactions[_txHash];
        require(txData.txHash != 0, "Transaction does not exist");
        require(
            txData.status == TxStatus.Verified,
            "Only verified transactions can be completed"
        );
        
        txData.status = TxStatus.Completed;
        emit TxCompleted(_txHash, block.timestamp);
    }
    
    /**
     * @dev Check if a transaction is on hold
     * @param _txHash The transaction hash to check
     * @return isHeld Whether the transaction is on hold
     * @return reason The reason for the hold (if any)
     */
    function isHeld(bytes32 _txHash) external view returns (bool isHeld, string memory reason) {
        Transaction memory txData = transactions[_txHash];
        return (txData.status == TxStatus.Held, txData.reason);
    }
    
    /**
     * @dev Get transaction status
     * @param _txHash The transaction hash to check
     * @return status The transaction status as a string
     */
    function getTransactionStatus(bytes32 _txHash) external view returns (string memory) {
        Transaction memory txData = transactions[_txHash];
        if (txData.txHash == 0) return "NOT_FOUND";
        
        if (txData.status == TxStatus.Pending) return "PENDING";
        if (txData.status == TxStatus.Held) return "HELD";
        if (txData.status == TxStatus.Verified) return "VERIFIED";
        if (txData.status == TxStatus.Rejected) return "REJECTED";
        if (txData.status == TxStatus.Completed) return "COMPLETED";
        
        return "UNKNOWN";
    }
    
    /**
     * @dev Add or remove an authorized relayer
     * @param _relayer The address of the relayer to update
     * @param _authorized Whether to authorize or deauthorize the relayer
     */
    function setRelayer(address _relayer, bool _authorized) external onlyOwner {
        require(_relayer != address(0), "Invalid relayer address");
        authorizedRelayers[_relayer] = _authorized;
        if (_authorized) {
            relayer = _relayer; // Set as primary relayer
        } else if (relayer == _relayer) {
            relayer = owner; // Fallback to owner if primary relayer is removed
        }
    }
    
    /**
     * @dev Transfer ownership of the contract
     * @param _newOwner The address of the new owner
     */
    function transferOwnership(address _newOwner) external onlyOwner {
        require(_newOwner != address(0), "Invalid new owner");
        owner = _newOwner;
    }
}
