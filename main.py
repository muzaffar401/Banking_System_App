import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import os
import uuid
import plotly.express as px
import time
from email_validator import validate_email, EmailNotValidError
import re

# Constants
DATA_FILE = "bank_data.json"
LOAN_INTEREST_RATE = 0.05  # 5% annual interest
FIXED_DEPOSIT_INTEREST = 0.07  # 7% annual interest
MIN_PASSWORD_LENGTH = 8
SESSION_TIMEOUT = 1800  # 30 minutes in seconds

# Initialize session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'accounts' not in st.session_state:
        st.session_state.accounts = {}
    if 'transactions' not in st.session_state:
        st.session_state.transactions = {}
    if 'transfer_data' not in st.session_state:
        st.session_state.transfer_data = {}
    if 'loans' not in st.session_state:
        st.session_state.loans = {}
    if 'fixed_deposits' not in st.session_state:
        st.session_state.fixed_deposits = {}
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    if 'failed_attempts' not in st.session_state:
        st.session_state.failed_attempts = {}

# Data persistence functions
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            st.session_state.accounts = data.get('accounts', {})
            st.session_state.transactions = data.get('transactions', {})
            st.session_state.loans = data.get('loans', {})
            st.session_state.fixed_deposits = data.get('fixed_deposits', {})
            st.session_state.failed_attempts = data.get('failed_attempts', {})

def save_data():
    data = {
        'accounts': st.session_state.accounts,
        'transactions': st.session_state.transactions,
        'loans': st.session_state.loans,
        'fixed_deposits': st.session_state.fixed_deposits,
        'failed_attempts': st.session_state.failed_attempts
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Security functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password_strength(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"

def validate_email_address(email):
    try:
        v = validate_email(email)
        return True, v.email
    except EmailNotValidError as e:
        return False, str(e)

def check_session_timeout():
    if st.session_state.login_time and st.session_state.authenticated:
        elapsed = time.time() - st.session_state.login_time
        if elapsed > SESSION_TIMEOUT:
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.warning("Session timed out due to inactivity. Please login again.")
            return True
    return False

# Account management
def create_account(username, password, email, initial_deposit=0):
    if username in st.session_state.accounts:
        return False, "Username already exists"

    # Check if email is already registered
    for user, data in st.session_state.accounts.items():
        if 'email' in data and data['email'] == email:
            return False, "Email already registered with another account"

    hashed_pw = hash_password(password)
    account_id = str(uuid.uuid4())[:8]  # Generate unique account ID

    st.session_state.accounts[username] = {
        'password': hashed_pw,
        'balance': int(initial_deposit),
        'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'account_id': account_id,
        'email': email,
        'last_login': None,
        'account_type': 'standard',
        'status': 'active'
    }

    if initial_deposit > 0:
        transaction_id = str(uuid.uuid4())
        record_transaction(username, 'Account Creation Deposit', initial_deposit, transaction_id)

    save_data()
    return True, f"Account created successfully! Your Account ID: {account_id}"

def authenticate(username, password):
    # Check if account is locked
    if username in st.session_state.failed_attempts:
        if st.session_state.failed_attempts[username]['count'] >= 5:
            last_attempt = st.session_state.failed_attempts[username]['timestamp']
            if (datetime.now() - datetime.strptime(last_attempt, "%Y-%m-%d %H:%M:%S")).seconds < 3600:  # 1 hour lock
                return False, "Account locked due to too many failed attempts. Try again later."

    if username not in st.session_state.accounts:
        return False, "Username not found"

    hashed_pw = hash_password(password)
    if st.session_state.accounts[username]['password'] != hashed_pw:
        # Record failed attempt
        if username not in st.session_state.failed_attempts:
            st.session_state.failed_attempts[username] = {'count': 0, 'timestamp': None}
        st.session_state.failed_attempts[username]['count'] += 1
        st.session_state.failed_attempts[username]['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data()

        remaining_attempts = 5 - st.session_state.failed_attempts[username]['count']
        if remaining_attempts <= 0:
            return False, "Account locked due to too many failed attempts. Try again later."
        return False, f"Incorrect password. {remaining_attempts} attempts remaining"

    # Reset failed attempts on successful login
    if username in st.session_state.failed_attempts:
        del st.session_state.failed_attempts[username]
        save_data()

    st.session_state.authenticated = True
    st.session_state.current_user = username
    st.session_state.login_time = time.time()
    st.session_state.accounts[username]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data()
    return True, "Login successful"

# Transaction functions
def record_transaction(username, transaction_type, amount, transaction_id=None, description=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not transaction_id:
        transaction_id = str(uuid.uuid4())

    if username not in st.session_state.transactions:
        st.session_state.transactions[username] = {}

    st.session_state.transactions[username][transaction_id] = {
        'type': transaction_type,
        'amount': int(amount),
        'timestamp': timestamp,
        'balance_after': st.session_state.accounts[username]['balance'],
        'transaction_id': transaction_id,
        'description': description
    }
    save_data()
    return transaction_id

def deposit(username, amount):
    if amount <= 0:
        return False, "Amount must be positive"

    st.session_state.accounts[username]['balance'] += amount
    transaction_id = record_transaction(username, 'Deposit', amount)
    return True, f"Deposited ${amount} successfully. Transaction ID: {transaction_id}"

def withdraw(username, amount):
    if amount <= 0:
        return False, "Amount must be positive"

    current_balance = st.session_state.accounts[username]['balance']
    if amount > current_balance:
        return False, "Insufficient funds"

    st.session_state.accounts[username]['balance'] -= amount
    transaction_id = record_transaction(username, 'Withdrawal', amount)
    return True, f"Withdrew ${amount} successfully. Transaction ID: {transaction_id}"

def initiate_transfer(sender_username, recipient_username, recipient_account_id, amount, description=None):
    # Check if recipient exists
    if recipient_username not in st.session_state.accounts:
        return False, "Recipient username not found"

    # Verify account ID matches
    recipient_account = st.session_state.accounts[recipient_username]
    if recipient_account['account_id'] != recipient_account_id:
        return False, "Account ID doesn't match the username"

    if sender_username == recipient_username:
        return False, "Cannot transfer to yourself"

    sender_balance = st.session_state.accounts[sender_username]['balance']
    if amount > sender_balance:
        return False, "Insufficient funds for transfer"

    # Store transfer details for confirmation
    transfer_id = str(uuid.uuid4())
    st.session_state.transfer_data[transfer_id] = {
        'sender': sender_username,
        'recipient': recipient_username,
        'recipient_account_id': recipient_account_id,
        'amount': amount,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'description': description
    }

    return True, transfer_id

def confirm_transfer(transfer_id):
    if transfer_id not in st.session_state.transfer_data:
        return False, "Invalid transfer request"

    transfer_details = st.session_state.transfer_data[transfer_id]
    sender = transfer_details['sender']
    recipient = transfer_details['recipient']
    amount = transfer_details['amount']
    description = transfer_details.get('description', None)

    # Perform the transfer
    st.session_state.accounts[sender]['balance'] -= amount
    st.session_state.accounts[recipient]['balance'] += amount

    # Record transactions
    transaction_id = str(uuid.uuid4())
    record_transaction(sender, 'Transfer Out', amount, transaction_id, description)
    record_transaction(recipient, 'Transfer In', amount, transaction_id, description)

    # Clear the transfer data
    del st.session_state.transfer_data[transfer_id]

    return True, f"Transferred ${amount} to {recipient} successfully. Transaction ID: {transaction_id}"

# Loan functions
def apply_for_loan(username, amount, duration_months):
    if amount <= 0:
        return False, "Loan amount must be positive"
    if duration_months <= 0:
        return False, "Loan duration must be positive"

    # Simple credit check - at least 3 months of account history
    account_created = datetime.strptime(st.session_state.accounts[username]['created'], "%Y-%m-%d %H:%M:%S")
    if (datetime.now() - account_created).days < 90:
        return False, "Account must be at least 3 months old to apply for a loan"

    # Check if user already has an active loan
    if username in st.session_state.loans:
        for loan_id, loan in st.session_state.loans[username].items():
            if loan['status'] == 'active':
                return False, "You already have an active loan"

    loan_id = str(uuid.uuid4())
    monthly_payment = calculate_monthly_payment(amount, duration_months)

    if username not in st.session_state.loans:
        st.session_state.loans[username] = {}

    st.session_state.loans[username][loan_id] = {
        'amount': amount,
        'duration_months': duration_months,
        'interest_rate': LOAN_INTEREST_RATE,
        'monthly_payment': monthly_payment,
        'remaining_balance': amount * (1 + LOAN_INTEREST_RATE),
        'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'active',
        'payments_made': 0
    }

    # Disburse loan amount to account
    st.session_state.accounts[username]['balance'] += amount
    record_transaction(username, 'Loan Disbursement', amount, description=f"Loan ID: {loan_id}")

    save_data()
    return True, f"Loan approved! ${amount} has been deposited to your account. Loan ID: {loan_id}"

def calculate_monthly_payment(principal, months):
    total_amount = principal * (1 + LOAN_INTEREST_RATE)
    return round(total_amount / months)

def make_loan_payment(username, loan_id, amount):
    if username not in st.session_state.loans or loan_id not in st.session_state.loans[username]:
        return False, "Loan not found"

    loan = st.session_state.loans[username][loan_id]
    if loan['status'] != 'active':
        return False, "Loan is not active"

    if amount <= 0:
        return False, "Payment amount must be positive"

    if amount > st.session_state.accounts[username]['balance']:
        return False, "Insufficient funds for payment"

    if amount < loan['monthly_payment']:
        return False, f"Minimum payment required: ${loan['monthly_payment']}"

    # Process payment
    st.session_state.accounts[username]['balance'] -= amount
    loan['remaining_balance'] -= amount
    loan['payments_made'] += 1

    # Record transaction
    record_transaction(username, 'Loan Payment', amount, description=f"Loan ID: {loan_id}")

    # Check if loan is fully paid
    if loan['remaining_balance'] <= 0:
        loan['status'] = 'paid'
        loan['end_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_data()
    return True, f"Payment of ${amount} applied to loan {loan_id}"

# Fixed Deposit functions
def create_fixed_deposit(username, amount, duration_months):
    if amount <= 0:
        return False, "Amount must be positive"
    if duration_months <= 0:
        return False, "Duration must be positive"

    if amount > st.session_state.accounts[username]['balance']:
        return False, "Insufficient funds for fixed deposit"

    fd_id = str(uuid.uuid4())
    maturity_amount = calculate_maturity_amount(amount, duration_months)

    if username not in st.session_state.fixed_deposits:
        st.session_state.fixed_deposits[username] = {}

    st.session_state.fixed_deposits[username][fd_id] = {
        'principal': amount,
        'duration_months': duration_months,
        'interest_rate': FIXED_DEPOSIT_INTEREST,
        'maturity_amount': maturity_amount,
        'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'maturity_date': (datetime.now() + timedelta(days=30*duration_months)).strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'active'
    }

    # Deduct from account balance
    st.session_state.accounts[username]['balance'] -= amount
    record_transaction(username, 'Fixed Deposit Creation', amount, description=f"FD ID: {fd_id}")

    save_data()
    return True, f"Fixed deposit created successfully! FD ID: {fd_id}"

def calculate_maturity_amount(principal, months):
    return round(principal * (1 + FIXED_DEPOSIT_INTEREST * (months/12)))

def close_fixed_deposit(username, fd_id):
    if username not in st.session_state.fixed_deposits or fd_id not in st.session_state.fixed_deposits[username]:
        return False, "Fixed deposit not found"

    fd = st.session_state.fixed_deposits[username][fd_id]
    if fd['status'] != 'active':
        return False, "Fixed deposit is not active"

    # Check if matured
    maturity_date = datetime.strptime(fd['maturity_date'], "%Y-%m-%d %H:%M:%S")
    if datetime.now() < maturity_date:
        return False, "Fixed deposit has not matured yet"

    # Credit amount to account
    st.session_state.accounts[username]['balance'] += fd['maturity_amount']
    record_transaction(username, 'Fixed Deposit Maturity', fd['maturity_amount'], description=f"FD ID: {fd_id}")

    # Update FD status
    fd['status'] = 'closed'
    fd['closed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_data()
    return True, f"Fixed deposit {fd_id} closed. ${fd['maturity_amount']} credited to your account"


# UI Components
def login_section():
    st.markdown("""
        <style>
            .login-container {
                max-width: 500px;
                margin: 0 auto;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                background-color: #ffffff;
            }
            .bank-header {
                text-align: center;
                margin-bottom: 2rem;
                color: #2c3e50;
            }
            .bank-logo {
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
            }
            .bank-subtitle {
                color: #7f8c8d;
                margin-bottom: 2rem;
            }
            .stButton>button {
                width: 100%;
                border-radius: 5px;
                padding: 0.5rem;
                font-weight: 500;
                background-color: #3498db;
                border: none;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #2980b9;
                transform: translateY(-2px);
            }
            .stTextInput>div>div>input {
                border-radius: 5px;
                padding: 0.5rem;
            }
            .stNumberInput>div>div>input {
                border-radius: 5px;
                padding: 0.5rem;
            }
            .stSelectbox>div>div>div {
                border-radius: 5px;
                padding: 0.5rem;
            }
            .tab-content {
                padding: 1rem 0;
            }
            .success-message {
                background-color: #d4edda;
                color: #155724;
                padding: 1rem;
                border-radius: 5px;
                margin-bottom: 1rem;
            }
            .error-message {
                background-color: #f8d7da;
                color: #721c24;
                padding: 1rem;
                border-radius: 5px;
                margin-bottom: 1rem;
            }
            .password-hint {
                font-size: 0.8rem;
                color: #7f8c8d;
                margin-top: -1rem;
                margin-bottom: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="login-container">
            <div class="bank-header">
                <div class="bank-logo">🏦</div>
                <h1>Advanced Banking System</h1>
                <div class="bank-subtitle">Secure, Reliable, and Convenient Banking</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.container():
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Login", type="primary")

                if submit:
                    success, message = authenticate(username, password)
                    if success:
                        st.markdown(f'<div class="success-message">{message}</div>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown(f'<div class="error-message">{message}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        with st.container():
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            with st.form("register_form"):
                new_username = st.text_input("Choose a username", placeholder="Enter a unique username")
                email = st.text_input("Email address", placeholder="Enter your email address")
                new_password = st.text_input("Choose a password", type="password", placeholder="Create a strong password")
                st.markdown('<div class="password-hint">Password must be at least 8 characters long with uppercase, lowercase, number, and special character</div>', unsafe_allow_html=True)
                confirm_password = st.text_input("Confirm password", type="password", placeholder="Confirm your password")
                initial_deposit = st.number_input("Initial deposit", min_value=0, value=0, step=1, help="Optional initial deposit amount")
                submit = st.form_submit_button("Create Account", type="primary")

                if submit:
                    if new_password != confirm_password:
                        st.markdown('<div class="error-message">Passwords don\'t match</div>', unsafe_allow_html=True)
                    else:
                        # Check password strength
                        pw_strong, pw_msg = check_password_strength(new_password)
                        if not pw_strong:
                            st.markdown(f'<div class="error-message">{pw_msg}</div>', unsafe_allow_html=True)
                            return

                        # Validate email
                        email_valid, email_msg = validate_email_address(email)
                        if not email_valid:
                            st.markdown(f'<div class="error-message">{email_msg}</div>', unsafe_allow_html=True)
                            return

                        success, message = create_account(new_username, new_password, email, initial_deposit)
                        if success:
                            st.markdown(f'<div class="success-message">{message}</div>', unsafe_allow_html=True)
                            st.warning("Please save your Account ID - you'll need it to receive transfers")
                        else:
                            st.markdown(f'<div class="error-message">{message}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

def dashboard():
    # Check session timeout
    if check_session_timeout():
        st.rerun()

    st.markdown("""
        <style>
            .dashboard-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
            }
            .account-card {
                background: linear-gradient(135deg, #3498db, #2c3e50);
                color: white;
                border-radius: 10px;
                padding: 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 1rem;
            }
            .account-card h3 {
                margin-top: 0;
                color: white;
            }
            .metric-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 1rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                margin-bottom: 1rem;
            }
            .metric-card h4 {
                margin-top: 0;
                color: #7f8c8d;
                font-size: 0.9rem;
            }
            .metric-value {
                font-size: 1.5rem;
                font-weight: bold;
                color: #2c3e50;
            }
            .operation-card {
                background-color: white;
                border-radius: 10px;
                padding: 1.5rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                margin-bottom: 2rem;
            }
            .transaction-row {
                display: flex;
                justify-content: space-between;
                padding: 0.75rem 0;
                border-bottom: 1px solid #eee;
            }
            .transaction-row:last-child {
                border-bottom: none;
            }
            .transaction-type {
                font-weight: 500;
            }
            .transaction-amount.positive {
                color: #27ae60;
            }
            .transaction-amount.negative {
                color: #e74c3c;
            }
            .loan-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 1rem;
                margin-bottom: 1rem;
            }
            .loan-status {
                display: inline-block;
                padding: 0.25rem 0.5rem;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 500;
            }
            .status-active {
                background-color: #d4edda;
                color: #155724;
            }
            .status-paid {
                background-color: #cce5ff;
                color: #004085;
            }
            .fd-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 1rem;
                margin-bottom: 1rem;
            }
            .progress-container {
                height: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
                margin: 0.5rem 0;
            }
            .progress-bar {
                height: 100%;
                border-radius: 4px;
                background-color: #3498db;
            }
            .logout-btn {
                position: fixed;
                bottom: 20px;
                right: 20px;
            }
            .stRadio>div {
                display: flex;
                gap: 1rem;
            }
            .stRadio>div>label {
                flex: 1;
                text-align: center;
                padding: 0.5rem;
                border-radius: 5px;
                border: 1px solid #ddd;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .stRadio>div>label:hover {
                background-color: #f8f9fa;
            }
            .stRadio>div>label[data-baseweb="radio"]>div:first-child {
                display: none;
            }
            .stRadio>div>label[data-baseweb="radio"]>div:last-child {
                width: 100%;
            }
            .stRadio>div>label[aria-checked="true"] {
                background-color: #3498db;
                color: white;
                border-color: #3498db;
            }
            .st-expander>div>div {
                border-radius: 10px;
                border: 1px solid #eee;
            }
            .st-expander>div>div:hover {
                border-color: #3498db;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="dashboard-header">
            <h1>Welcome back, {st.session_state.current_user}</h1>
            <div class="last-login">Last login: {st.session_state.accounts[st.session_state.current_user].get('last_login', 'Never')}</div>
        </div>
    """, unsafe_allow_html=True)

    # Display account info with error handling
    if st.session_state.current_user in st.session_state.accounts:
        account = st.session_state.accounts[st.session_state.current_user]

        # Account summary
        st.markdown(f"""
            <div class="account-card">
                <h3>Account Overview</h3>
                <div style="font-size: 2.5rem; font-weight: bold;">${account.get('balance', 0):,.2f}</div>
                <div style="margin-top: 1rem;">
                    <span style="color: #bdc3c7;">Account ID:</span> {account.get('account_id', 'N/A')}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Quick actions
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <h4>Account Type</h4>
                    <div class="metric-value">{account.get('account_type', 'Standard').title()}</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <h4>Account Created</h4>
                    <div class="metric-value">{account.get('created', 'N/A')}</div>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <h4>Account Status</h4>
                    <div class="metric-value">{account.get('status', 'Active').title()}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.error("Account information not found")
        return

    # Operations
    st.markdown("""
        <style>
            .operation-tabs {
                margin: 2rem 0;
            }
        </style>
    """, unsafe_allow_html=True)

    operation = st.radio(
        "Select Operation",
        ["Deposit", "Withdraw", "Transfer", "Transaction History", "Loans", "Fixed Deposits"],
        horizontal=True,
        label_visibility="hidden"
    )

    st.divider()

    if operation == "Deposit":
        with st.container():
            st.markdown('<div class="operation-card">', unsafe_allow_html=True)
            st.subheader("Deposit Funds")
            with st.form("deposit_form"):
                amount = st.number_input("Amount to deposit", min_value=1, step=1, format="%d")
                submit = st.form_submit_button("Deposit", type="primary")
                if submit:
                    success, message = deposit(st.session_state.current_user, amount)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            st.markdown('</div>', unsafe_allow_html=True)

    elif operation == "Withdraw":
        with st.container():
            st.markdown('<div class="operation-card">', unsafe_allow_html=True)
            st.subheader("Withdraw Funds")
            with st.form("withdraw_form"):
                amount = st.number_input("Amount to withdraw", min_value=1, step=1, format="%d")
                submit = st.form_submit_button("Withdraw", type="primary")
                if submit:
                    success, message = withdraw(st.session_state.current_user, amount)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            st.markdown('</div>', unsafe_allow_html=True)

    elif operation == "Transfer":
        if 'transfer_confirmation' not in st.session_state:
            st.session_state.transfer_confirmation = False

        with st.container():
            st.markdown('<div class="operation-card">', unsafe_allow_html=True)
            if not st.session_state.transfer_confirmation:
                st.subheader("Transfer Funds")
                with st.form("transfer_init_form"):
                    recipient_username = st.text_input("Recipient Username", placeholder="Enter recipient's username")
                    recipient_account_id = st.text_input("Recipient Account ID", placeholder="Enter recipient's account ID")
                    amount = st.number_input("Amount to transfer", min_value=1, step=1, format="%d")
                    description = st.text_input("Description (optional)", placeholder="Add a note for the recipient")
                    submit = st.form_submit_button("Initiate Transfer", type="primary")

                    if submit:
                        success, result = initiate_transfer(
                            st.session_state.current_user,
                            recipient_username,
                            recipient_account_id,
                            amount,
                            description
                        )
                        if success:
                            st.session_state.transfer_id = result
                            st.session_state.transfer_confirmation = True
                            st.session_state.transfer_recipient = recipient_username
                            st.session_state.transfer_amount = amount
                            st.rerun()
                        else:
                            st.error(result)
            else:
                st.subheader("Confirm Transfer")
                st.markdown(f"""
                    <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                            <div style="font-weight: 500;">Recipient:</div>
                            <div>{st.session_state.transfer_recipient}</div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                            <div style="font-weight: 500;">Amount:</div>
                            <div style="font-weight: bold; font-size: 1.2rem;">${st.session_state.transfer_amount:,.2f}</div>
                        </div>
                """, unsafe_allow_html=True)

                transfer_details = st.session_state.transfer_data[st.session_state.transfer_id]
                if transfer_details.get('description'):
                    st.markdown(f"""
                        <div style="display: flex; justify-content: space-between;">
                            <div style="font-weight: 500;">Description:</div>
                            <div>{transfer_details['description']}</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Confirm Transfer", type="primary"):
                        success, message = confirm_transfer(st.session_state.transfer_id)
                        if success:
                            st.success(message)
                            st.session_state.transfer_confirmation = False
                            st.rerun()
                        else:
                            st.error(message)
                with col2:
                    if st.button("Cancel"):
                        st.session_state.transfer_confirmation = False
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    elif operation == "Transaction History":
        with st.container():
            st.subheader("Transaction History")
        
        # CSS styling in markdown
        st.markdown("""
        <style>
            .transaction-container {
                margin-top: 1rem;
            }
            .transaction-row {
                display: flex;
                justify-content: space-between;
                padding: 0.75rem 0;
                border-bottom: 1px solid #eee;
            }
            .transaction-row:last-child {
                border-bottom: none;
            }
            .transaction-type {
                font-weight: 500;
            }
            .transaction-details {
                font-size: 0.8rem;
                color: #7f8c8d;
            }
            .transaction-description {
                font-size: 0.8rem;
                margin-top: 0.25rem;
            }
            .transaction-amount {
                font-weight: bold;
                font-size: 1.1rem;
            }
            .positive {
                color: #27ae60;
            }
            .negative {
                color: #e74c3c;
            }
        </style>
        """, unsafe_allow_html=True)

        if st.session_state.current_user not in st.session_state.transactions:
            st.write("No transactions yet.")
        else:
            user_transactions = [
                {**tx, 'id': tx_id}
                for tx_id, tx in st.session_state.transactions[st.session_state.current_user].items()
            ]

            if not user_transactions:
                st.write("No transactions yet.")
            else:
                df = pd.DataFrame(user_transactions)
                df = df.sort_values('timestamp', ascending=False)

                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    transaction_type = st.selectbox(
                        "Filter by type",
                        ["All"] + list(df['type'].unique()),
                        index=0
                    )
                with col2:
                    date_range = st.selectbox(
                        "Filter by date range",
                        ["All time", "Last 7 days", "Last 30 days", "Last 90 days"],
                        index=0
                    )

                # Apply filters
                if transaction_type != "All":
                    df = df[df['type'] == transaction_type]

                if date_range != "All time":
                    days = 7 if date_range == "Last 7 days" else 30 if date_range == "Last 30 days" else 90
                    cutoff_date = datetime.now() - timedelta(days=days)
                    df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
                    df = df[df['timestamp_dt'] >= cutoff_date]

                # Display transactions
                if df.empty:
                    st.write("No transactions match your filters.")
                else:
                    # Show summary statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Transactions", len(df))
                    with col2:
                        st.metric("Total Deposits", f"${df[df['type'] == 'Deposit']['amount'].sum():,.2f}")
                    with col3:
                        st.metric("Total Withdrawals", f"${df[df['type'] == 'Withdrawal']['amount'].sum():,.2f}")

                    # Show transaction list using Streamlit components
                    for _, row in df.iterrows():
                        amount_class = "positive" if row['type'] in ['Deposit', 'Transfer In'] else "negative"
                        
                        # Create columns for the transaction row
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{row['type']}**")
                            st.caption(row['timestamp'])
                            if row['description']:
                                st.caption(row['description'])
                        with col2:
                            st.markdown(f"<div class='transaction-amount {amount_class}'>${row['amount']:,.2f}</div>", 
                                       unsafe_allow_html=True)
                        
                        # Add divider between transactions
                        st.divider()

                    # Show transaction trend chart
                    st.subheader("Transaction Trend")
                    df_chart = df.copy()
                    df_chart['date'] = pd.to_datetime(df_chart['timestamp']).dt.date
                    df_chart = df_chart.groupby(['date', 'type'])['amount'].sum().unstack().fillna(0)

                    fig = px.line(df_chart, title="Daily Transaction Amounts")
                    st.plotly_chart(fig)

    elif operation == "Loans":
        with st.container():
            st.markdown('<div class="operation-card">', unsafe_allow_html=True)
            loan_tab1, loan_tab2 = st.tabs(["Apply for Loan", "My Loans"])

            with loan_tab1:
                st.subheader("Apply for Loan")
                with st.form("loan_application"):
                    amount = st.number_input("Loan Amount", min_value=100, step=100, format="%d")
                    duration = st.selectbox("Loan Duration (months)", [6, 12, 24, 36, 48, 60])
                    submit = st.form_submit_button("Apply", type="primary")

                    if submit:
                        success, message = apply_for_loan(
                            st.session_state.current_user, amount, duration)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            with loan_tab2:
                st.subheader("My Loans")
                if st.session_state.current_user not in st.session_state.loans or not st.session_state.loans[st.session_state.current_user]:
                    st.write("You don't have any loans.")
                else:
                    for loan_id, loan in st.session_state.loans[st.session_state.current_user].items():
                        status_class = "status-active" if loan['status'] == 'active' else "status-paid"
                        with st.expander(f"Loan {loan_id} - {loan['status'].title()}"):
                            st.markdown(f"""
                                <div class="loan-card">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                        <div>
                                            <span class="loan-status {status_class}">{loan['status'].title()}</span>
                                        </div>
                                        <div style="font-size: 1.2rem; font-weight: bold;">${loan['remaining_balance']:,.2f}</div>
                                    </div>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                                        <div>
                                            <div style="font-size: 0.8rem; color: #7f8c8d;">Original Amount</div>
                                            <div style="font-weight: 500;">${loan['amount']:,.2f}</div>
                                        </div>
                                        <div>
                                            <div style="font-size: 0.8rem; color: #7f8c8d;">Duration</div>
                                            <div style="font-weight: 500;">{loan['duration_months']} months</div>
                                        </div>
                                        <div>
                                            <div style="font-size: 0.8rem; color: #7f8c8d;">Interest Rate</div>
                                            <div style="font-weight: 500;">{loan['interest_rate']*100}%</div>
                                        </div>
                                        <div>
                                            <div style="font-size: 0.8rem; color: #7f8c8d;">Monthly Payment</div>
                                            <div style="font-weight: 500;">${loan['monthly_payment']:,.2f}</div>
                                        </div>
                                    </div>
                                    <div style="margin-bottom: 1rem;">
                                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                                            <div>Progress</div>
                                            <div>{loan['payments_made']}/{loan['duration_months']} payments</div>
                                        </div>
                                        <div class="progress-container">
                                            <div class="progress-bar" style="width: {loan['payments_made']/loan['duration_months']*100}%"></div>
                                        </div>
                                    </div>
                            """, unsafe_allow_html=True)

                            if loan['status'] == 'active':
                                with st.form(f"loan_payment_{loan_id}"):
                                    payment_amount = st.number_input(
                                        "Payment Amount",
                                        min_value=loan['monthly_payment'],
                                        value=loan['monthly_payment'],
                                        step=10,
                                        key=f"payment_{loan_id}"
                                    )
                                    submit_payment = st.form_submit_button(
                                        "Make Payment", type="primary"
                                    )
                                    if submit_payment:
                                        success, message = make_loan_payment(
                                            st.session_state.current_user,
                                            loan_id,
                                            payment_amount
                                        )
                                        if success:
                                            st.success(message)
                                            st.rerun()
                                        else:
                                            st.error(message)
                            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif operation == "Fixed Deposits":
        with st.container():
            st.markdown('<div class="operation-card">', unsafe_allow_html=True)
            fd_tab1, fd_tab2 = st.tabs(["Create Fixed Deposit", "My Fixed Deposits"])

            with fd_tab1:
                st.subheader("Create Fixed Deposit")
                with st.form("fd_creation"):
                    amount = st.number_input("Amount", min_value=100, step=100, format="%d")
                    duration = st.selectbox("Duration (months)", [3, 6, 12, 24, 36])
                    submit = st.form_submit_button("Create", type="primary")

                    if submit:
                        success, message = create_fixed_deposit(
                            st.session_state.current_user, amount, duration)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            with fd_tab2:
                st.subheader("My Fixed Deposits")
                if st.session_state.current_user not in st.session_state.fixed_deposits or not st.session_state.fixed_deposits[st.session_state.current_user]:
                    st.write("You don't have any fixed deposits.")
                else:
                    for fd_id, fd in st.session_state.fixed_deposits[st.session_state.current_user].items():
                        with st.expander(f"FD {fd_id} - {fd['status'].title()}"):
                            st.markdown(f"""
                                <div class="fd-card">
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                                        <div>
                                            <div style="font-size: 0.8rem; color: #7f8c8d;">Principal</div>
                                            <div style="font-weight: 500;">${fd['principal']:,.2f}</div>
                                        </div>
                                        <div>
                                            <div style="font-size: 0.8rem; color: #7f8c8d;">Duration</div>
                                            <div style="font-weight: 500;">{fd['duration_months']} months</div>
                                        </div>
                                        <div>
                                            <div style="font-size: 0.8rem; color: #7f8c8d;">Interest Rate</div>
                                            <div style="font-weight: 500;">{fd['interest_rate']*100}%</div>
                                        </div>
                                        <div>
                                            <div style="font-size: 0.8rem; color: #7f8c8d;">Maturity Amount</div>
                                            <div style="font-weight: 500;">${fd['maturity_amount']:,.2f}</div>
                                        </div>
                                    </div>
                                    <div style="margin-bottom: 1rem;">
                                        <div style="font-size: 0.8rem; color: #7f8c8d;">Start Date</div>
                                        <div style="font-weight: 500;">{fd['start_date']}</div>
                                    </div>
                                    <div style="margin-bottom: 1rem;">
                                        <div style="font-size: 0.8rem; color: #7f8c8d;">Maturity Date</div>
                                        <div style="font-weight: 500;">{fd['maturity_date']}</div>
                                    </div>
                            """, unsafe_allow_html=True)

                            if fd['status'] == 'active':
                                maturity_date = datetime.strptime(fd['maturity_date'], "%Y-%m-%d %H:%M:%S")
                                if datetime.now() >= maturity_date:
                                    if st.button("Close Fixed Deposit", key=f"close_{fd_id}"):
                                        success, message = close_fixed_deposit(
                                            st.session_state.current_user, fd_id)
                                        if success:
                                            st.success(message)
                                            st.rerun()
                                        else:
                                            st.error(message)
                                else:
                                    days_remaining = (maturity_date - datetime.now()).days
                                    st.markdown(f"""
                                        <div style="margin-top: 1rem;">
                                            <div style="font-size: 0.8rem; color: #7f8c8d;">Days to Maturity</div>
                                            <div style="font-weight: 500;">{days_remaining} days</div>
                                        </div>
                                    """, unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # Logout button
    st.markdown("""
        <div class="logout-btn">
            <style>
                .logout-btn button {
                    border-radius: 20px;
                    padding: 0.5rem 1rem;
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    transition: all 0.3s ease;
                }
                .logout-btn button:hover {
                    background-color: #c0392b;
                    transform: translateY(-2px);
                }
            </style>
    """, unsafe_allow_html=True)
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.transfer_confirmation = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Main App
def main():
    # Initialize session state
    init_session_state()

    # Load data at startup
    load_data()

    # Set page config
    st.set_page_config(
        page_title="Advanced Banking System",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Add custom CSS
    st.markdown("""
        <style>
            /* Main content styling */
            .stApp {
                background-color: #f5f7fa;
            }
            /* Input field focus styling */
            .stTextInput>div>div>input:focus, 
            .stNumberInput>div>div>input:focus, 
            .stSelectbox>div>div>select:focus {
                border-color: #3498db !important;
                box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2) !important;
            }
            /* Button hover effects */
            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            /* Tab styling */
            [data-baseweb="tab-list"] {
                gap: 1rem;
            }
            [data-baseweb="tab"] {
                padding: 0.5rem 1rem;
                border-radius: 5px;
                transition: all 0.3s ease;
            }
            [data-baseweb="tab"]:hover {
                background-color: #f8f9fa;
            }
            [aria-selected="true"] {
                background-color: #3498db !important;
                color: white !important;
            }
            /* Metric cards */
            [data-testid="stMetric"] {
                border: 1px solid #eee;
                border-radius: 10px;
                padding: 1rem;
                transition: all 0.3s ease;
            }
            [data-testid="stMetric"]:hover {
                border-color: #3498db;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }
            /* Expander styling */
            .st-expander {
                border: 1px solid #eee;
                border-radius: 10px;
                padding: 1rem;
            }
            .st-expander:hover {
                border-color: #3498db;
            }
            /* Dataframe styling */
            .stDataFrame {
                border-radius: 10px;
                overflow: hidden;
            }
            /* Remove Streamlit branding */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    # Show appropriate section based on auth status
    if st.session_state.authenticated:
        dashboard()
    else:
        login_section()

if __name__ == "__main__":
    main()