// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const transactionForm = document.getElementById('transactionForm');
const riskCard = document.getElementById('riskCard');

// Initialize the application
function init() {
    // Add event listeners
    transactionForm.addEventListener('submit', handleSubmit);
    
    // Check if Web3 is injected (MetaMask)
    if (typeof window.ethereum !== 'undefined') {
        console.log('MetaMask is installed!');
        window.web3 = new Web3(window.ethereum);
    } else {
        console.warn('No Web3 provider detected. Please install MetaMask!');
    }
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();
    
    // Get form data
    const formData = {
        sender_phone_hash: hashPhoneNumber(document.getElementById('senderPhone').value),
        receiver_phone_hash: hashPhoneNumber(document.getElementById('recipientPhone').value),
        amount: parseFloat(document.getElementById('amount').value),
        tx_type: document.getElementById('transactionType').value,
        location: document.getElementById('location').value,
        // Add mock data for other required fields
        tx_id: 'TX' + Math.random().toString(36).substr(2, 9).toUpperCase(),
        time: new Date().toISOString(),
        device_id_hash: 'device_' + Math.random().toString(36).substr(2, 9),
        account_age_days: Math.floor(Math.random() * 3650) + 1, // 1-10 years
        previous_disputes: Math.floor(Math.random() * 3), // 0-2 disputes
        merchant_id: document.getElementById('transactionType').value === 'buy' ? 'M' + Math.floor(Math.random() * 100).toString().padStart(5, '0') : null
    };
    
    try {
        // Show loading state
        showLoading(true);
        
        // Call the prediction API
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Display the risk assessment
        displayRiskAssessment(result, formData);
        
        // If high risk, submit to blockchain
        if (result.risk_label === 'high') {
            await submitToBlockchain(formData, result);
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing your request. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Display risk assessment results
function displayRiskAssessment(result, formData) {
    const riskLevels = {
        low: { class: 'risk-low', label: 'Low Risk', icon: 'check-circle' },
        medium: { class: 'risk-medium', label: 'Medium Risk', icon: 'exclamation-triangle' },
        high: { class: 'risk-high', label: 'High Risk', icon: 'exclamation-circle' }
    };
    
    const risk = riskLevels[result.risk_label] || riskLevels.low;
    
    // Create risk card HTML
    riskCard.className = `risk-card ${risk.class} p-6 rounded-lg shadow-md`;
    riskCard.innerHTML = `
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold">Risk Assessment</h3>
            <span class="status-indicator status-${result.risk_label}">
                <i class="fas fa-${risk.icon} mr-1"></i>
                ${risk.label}
            </span>
        </div>
        
        <div class="mb-4">
            <div class="flex justify-between text-sm mb-1">
                <span>Risk Score</span>
                <span class="font-medium">${Math.round(result.risk_score * 100)}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div class="h-2.5 rounded-full ${risk.class.replace('risk-', 'bg-')}" 
                     style="width: ${result.risk_score * 100}%;"></div>
            </div>
        </div>
        
        <div class="space-y-3 mb-6">
            <h4 class="font-medium">Risk Factors:</h4>
            <ul class="space-y-2">
                ${result.explanation.split('. ').filter(Boolean).map(factor => 
                    `<li class="flex items-start">
                        <i class="fas fa-${risk.icon} mt-1 mr-2"></i>
                        <span>${factor.trim()}</span>
                    </li>`
                ).join('')}
            </ul>
        </div>
        
        <div id="actionButtons" class="space-y-3">
            <button id="proceedBtn" class="w-full btn btn-${result.risk_label === 'high' ? 'danger' : 'success'}">
                ${result.risk_label === 'high' ? 'Proceed with Caution' : 'Proceed with Transaction'}
            </button>
            <button id="cancelBtn" class="w-full bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300">
                Cancel
            </button>
        </div>
        
        <div id="blockchainStatus" class="mt-4 pt-4 border-t border-gray-200 hidden">
            <h4 class="font-medium mb-2">Blockchain Verification</h4>
            <div class="flex items-center space-x-2 text-sm">
                <div id="statusIcon" class="w-5 h-5 rounded-full bg-gray-300 flex items-center justify-center">
                    <i class="fas fa-spinner fa-spin text-xs"></i>
                </div>
                <span id="statusText">Verifying transaction on blockchain...</span>
            </div>
        </div>
    `;
    
    // Add event listeners to buttons
    document.getElementById('proceedBtn').addEventListener('click', () => handleProceed(result, formData));
    document.getElementById('cancelBtn').addEventListener('click', resetForm);
    
    // Show the risk card
    riskCard.classList.remove('hidden');
}

// Handle proceed button click
async function handleProceed(result, formData) {
    if (result.risk_label === 'high') {
        await submitToBlockchain(formData, result);
    } else {
        // For low/medium risk, proceed directly
        alert('Transaction submitted successfully!');
        resetForm();
    }
}

// Submit transaction to blockchain
async function submitToBlockchain(formData, riskResult) {
    const blockchainStatus = document.getElementById('blockchainStatus');
    const statusIcon = document.getElementById('statusIcon');
    const statusText = document.getElementById('statusText');
    
    // Show blockchain status
    blockchainStatus.classList.remove('hidden');
    statusIcon.innerHTML = '<i class="fas fa-spinner fa-spin text-xs"></i>';
    statusText.textContent = 'Submitting transaction to blockchain...';
    
    try {
        // In a real app, this would interact with your smart contract
        // For demo purposes, we'll simulate the blockchain interaction
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Simulate blockchain verification
        const isVerified = Math.random() > 0.3; // 70% chance of verification
        
        if (isVerified) {
            statusIcon.innerHTML = '<i class="fas fa-check text-green-500"></i>';
            statusText.textContent = 'Transaction verified on blockchain!';
            
            // Show success message
            await new Promise(resolve => setTimeout(resolve, 1500));
            alert('Transaction submitted and verified on blockchain!');
            resetForm();
        } else {
            statusIcon.innerHTML = '<i class="fas fa-times text-red-500"></i>';
            statusText.textContent = 'Transaction verification failed!';
            
            // Show error message
            await new Promise(resolve => setTimeout(resolve, 1500));
            alert('Transaction verification failed. Please try again or contact support.');
        }
    } catch (error) {
        console.error('Blockchain error:', error);
        statusIcon.innerHTML = '<i class="fas fa-times text-red-500"></i>';
        statusText.textContent = 'Error connecting to blockchain';
    }
}

// Reset the form
function resetForm() {
    transactionForm.reset();
    riskCard.classList.add('hidden');
}

// Show/hide loading state
function showLoading(isLoading) {
    const submitBtn = transactionForm.querySelector('button[type="submit"]');
    
    if (isLoading) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Processing...';
    } else {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Check Transaction Risk';
    }
}

// Helper function to hash phone numbers
function hashPhoneNumber(phone) {
    // In a real app, use a proper hashing function with a salt
    return 'hash_' + btoa(phone).replace(/[^a-zA-Z0-9]/g, '').substr(0, 20);
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', init);
