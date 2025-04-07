# 🏦 Advanced Banking System

![Banking System Screenshot](![image](https://github.com/user-attachments/assets/e0c5bca9-4b34-46a1-ba19-473cc78f2926))

Welcome to the **Advanced Banking System**, a modern, secure, and feature-rich banking web application developed using **Streamlit**. This project simulates real-world banking operations with a focus on robust security, interactive dashboards, and an intuitive user interface.

---

## 🌟 Key Features

### 🔒 Secure Authentication System
Your data security is our top priority. The system includes:
- **Multi-factor Credential Validation** – Basic verification of identity through credentials.
- **Password Strength Enforcement** – Passwords must be at least 8 characters long and include uppercase, lowercase, numbers, and special characters.
- **Account Lockout Mechanism** – Accounts are locked for 1 hour after 5 consecutive failed login attempts.
- **Session Timeout** – Auto-logout after 30 minutes of inactivity for user safety.
- **Email Validation** – Ensures only valid emails can register using the `email-validator` library.

### 💰 Core Banking Operations
Manage your finances seamlessly:
- **Deposit and Withdraw Funds** – With every transaction recorded.
- **Account-to-Account Transfers** – Includes confirmation to avoid accidental transactions.
- **Comprehensive Transaction History** – Search, filter, and view detailed records.
- **Transaction Analytics** – Visualized using Plotly for trend analysis.

### 🏦 Loan Management
Plan and manage loans efficiently:
- **Loan Application System** – Apply for loans with basic credit validation.
- **Loan Calculator** – Get real-time calculations of EMIs and interest.
- **Loan Tracking Dashboard** – Visual representation of repayment progress.
- **Secure Loan Payment Processing** – Ensures integrity of every payment.

### 💹 Fixed Deposit System
Grow your wealth with fixed deposits:
- **Create Flexible FDs** – Choose from 3 to 36 months.
- **Interest Calculation** – Based on a 7% annual interest rate.
- **Maturity Countdown** – Track remaining days to maturity.
- **Auto-Close on Maturity** – Automatically settle matured deposits.

### 📊 Dashboards & Analytics
Stay informed with smart dashboards:
- **Account Overview** – Balance cards and key stats.
- **Transaction Trends** – Daily, weekly, monthly analytics.
- **Financial Metrics** – Income vs Expense, saving rate, etc.
- **Responsive UI** – Accessible across mobile, tablet, and desktop.

---

## 🛠️ Technical Implementation

### 🧩 Tech Stack
- **Frontend/UI**: [Streamlit](https://streamlit.io/) + custom CSS
- **Backend/Storage**: JSON file-based storage system
- **Security**: SHA-256 password hashing, session and input validation
- **Visualization**: Plotly Express for interactive charts
- **Utilities**: UUID, datetime, hashlib, email-validator

### 🗄️ Data Structure Overview
```json
{
  "accounts": {
    "username": {
      "password": "hashed",
      "balance": 0,
      "account_id": "uuid",
      "email": "validated",
      "account_type": "standard",
      "status": "active"
    }
  },
  "transactions": {
    "username": {
      "transaction_id": {
        "type": "Deposit/Withdrawal/Transfer",
        "amount": 100,
        "timestamp": "ISO",
        "balance_after": 100,
        "description": "optional"
      }
    }
  },
  "loans": {
    "username": {
      "loan_id": {
        "amount": 1000,
        "duration_months": 12,
        "interest_rate": 0.05,
        "remaining_balance": 1050,
        "status": "active/paid"
      }
    }
  },
  "fixed_deposits": {
    "username": {
      "fd_id": {
        "principal": 1000,
        "duration_months": 12,
        "maturity_amount": 1070,
        "status": "active/closed"
      }
    }
  }
}
```

---

## 🚀 Getting Started

### ✅ Prerequisites
- Python 3.7+
- `pip` package manager

### 📦 Installation
1. **Clone the Repository**
```bash
git clone https://github.com/muzaffar401/Banking_System_App.git
cd Banking_System_App
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the App**
```bash
streamlit run main.py
```

> Access the app at: [http://localhost:8501](http://localhost:8501)

---

## 🧑‍💻 Usage Guide

### 👤 For Customers
- Register with a valid email and strong password
- Log in to view your dashboard
- Make deposits and withdrawals
- Transfer money to other users
- Apply for loans and manage fixed deposits
- Analyze your spending with the dashboard

### 👨‍💻 For Developers
- Uses `bank_data.json` for persistent storage
- SHA-256 hashing for storing passwords securely
- Maintains user session using Streamlit's `session_state`
- CSS customization to enhance UI/UX

---

## 🛡️ Security Features
| Feature              | Implementation           | Benefit                          |
|----------------------|---------------------------|----------------------------------|
| Password Hashing     | SHA-256                   | Protects credentials             |
| Account Lockout      | 5 failed attempts         | Prevents brute-force attacks     |
| Session Timeout      | 30 minutes                | Prevents unauthorized access     |
| Input Validation     | Email & Password Rules    | Data Integrity                   |
| Transaction IDs      | UUID                      | Transparent audit trails         |

---

## 📈 Future Enhancements
- 🔧 Admin Dashboard for User Management
- 📱 Mobile App Integration via API
- 🔐 Two-Factor Authentication (SMS/Email)
- 💱 Currency Exchange Module
- 📈 Investment Portfolio Tracker
- 🤖 AI Chatbot for Customer Support

---

## 📜 License
This project is licensed under the **MIT License**. See the LICENSE file for details.

---

## 🙏 Acknowledgments
- 💡 Streamlit – for the intuitive web framework
- 📊 Plotly – for interactive charts
- 🐍 Python Community – for libraries and open-source contributions

<div align="center">
  Made with ❤️ using Python & Streamlit
</div>

---

## 📝 How to Use This README
- Save this content as `README.md` in your project root directory
- Replace the placeholder image with actual screenshots
- Update `git clone` URL with your actual repository URL
- Add any project-specific sections or instructions as needed
- Bonus: Add GIF demos, badges (build, license, version), etc. for more flair!

---

> ✨ This README is designed to provide a comprehensive overview of your project, both for users and developers. It's clean, informative, and ready to be published with your app!

