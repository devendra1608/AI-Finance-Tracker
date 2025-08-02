# 💰 Dabba Expense Tracker - Streamlit Login Application

A beautiful and modern expense tracking application built with Streamlit, featuring user authentication and financial dashboard visualization with real-time data from MySQL database.

## 🚀 Features

- **🔐 Secure User Authentication**: Login system using email and password
- **💰 Real Financial Dashboard**: Visualize actual income, expenses, and financial trends from your database
- **📊 Interactive Charts**: Pie charts for expense categories and line charts for trends
- **📱 Responsive Design**: Modern UI with beautiful styling
- **🗄️ MySQL Database**: Direct connection to XAMPP MySQL database
- **📈 Real Transaction Data**: Fetch and display actual user transactions

## 📋 Demo Accounts

You can use any of these accounts to test the application:

| Email | Password |
|-------|----------|
| himnish@gmail.com | himnish@123 |
| rishi@gmail.com | rishi@123 |
| surya@gmail.com | surya@123 |
| sandeep@gmail.com | sandeep@123 |
| shaura@gmail.com | shaura@123 |

## 🛠️ Installation

1. **Ensure XAMPP is running** with MySQL service on port 3307
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** and navigate to `http://localhost:8501`

## 📁 Project Structure

```
PR/
├── app.py              # Main Streamlit application
├── dabba.sql          # Database schema and data
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── venv/              # Virtual environment (if used)
```

## 🔧 How It Works

1. **Database Connection**: The application connects directly to your XAMPP MySQL database (`Dabba`)
2. **Login System**: Users authenticate using email and password from the Users table
3. **Real Data Dashboard**: After successful login, users see their actual financial data:
   - Real financial metrics (income, expenses, balance)
   - Interactive charts with actual transaction data
   - Recent transaction history from database
   - Category-wise expense breakdown
   - Monthly trends analysis

## 🎨 Features

### Login Page
- Clean, modern login form
- Demo account credentials displayed
- Error handling for invalid credentials
- Success/error messages

### Dashboard
- **Financial Overview**: Real metrics from database displayed in cards
- **Expense Categories**: Pie chart showing actual expense distribution
- **Monthly Trends**: Line chart comparing real income vs expenses
- **Recent Transactions**: Data table with actual transaction history
- **Transaction Statistics**: Detailed analysis of user's financial data
- **Payment Methods**: Chart showing transaction distribution by payment mode
- **Logout Functionality**: Secure session management

## 🛡️ Security Features

- Session state management for authentication
- Password field masking
- SQL injection prevention using parameterized queries
- Secure logout functionality
- Direct MySQL connection with error handling

## 📊 Data Visualization

The application uses Plotly for interactive charts with real data:
- **Pie Charts**: For actual expense category distribution
- **Line Charts**: For real income vs expense trends
- **Bar Charts**: For payment method analysis
- **Metrics Cards**: For key financial indicators
- **Data Tables**: For transaction history with formatting

## 🔄 Session Management

- Persistent login state using Streamlit session state
- Automatic logout on button click
- Session data cleared on logout

## 🗄️ Database Requirements

- **XAMPP** with MySQL running on port 3307
- **Database**: `Dabba` (case-sensitive)
- **Tables**: `Users` and `Data` tables as per dabba.sql
- **Connection**: root user with no password (default XAMPP setup)

## 🎯 Real Data Features

- **User Authentication**: Real user login with database validation
- **Transaction History**: Actual transaction data from Data table
- **Financial Analytics**: Real calculations based on user's transactions
- **Category Analysis**: Actual expense breakdown by category
- **Trend Analysis**: Real monthly income vs expense trends
- **Payment Analysis**: Actual transaction distribution by payment method

## 🐛 Troubleshooting

If you encounter any issues:

1. **Database connection errors**: 
   - Ensure XAMPP is running
   - Check MySQL is on port 3307
   - Verify database name is `Dabba` (case-sensitive)
   - Ensure dabba.sql has been imported

2. **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`

3. **Port conflicts**: Use `streamlit run app.py --server.port 8502` to change port

4. **No data showing**: Check if the user has transactions in the Data table

## 📝 License

This project is for educational and demonstration purposes.

---

**Enjoy tracking your expenses with Dabba! 💰📊** 