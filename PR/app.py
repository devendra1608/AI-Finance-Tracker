import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import mysql.connector
from mysql.connector import Error
import requests
import json

# Page configuration
st.set_page_config(
    page_title="Dabba - Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

def get_mysql_connection():
    """Create MySQL connection to XAMPP database"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,  # Default XAMPP MySQL port
            database='dabba',
            user='root',
            password=''
        )
        return connection
    except Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        return None

def authenticate_user(email, password):
    """Authenticate user with email and password from MySQL database"""
    connection = get_mysql_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT user_id, Name, email, password 
            FROM Users 
            WHERE email = %s AND password = %s
        ''', (email, password))
        
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return user
    except Error as e:
        st.error(f"Database error: {e}")
        return None

def get_user_data(user_id):
    """Get user's expense data from MySQL database"""
    connection = get_mysql_connection()
    if connection is None:
        return pd.DataFrame()
    
    try:
        query = '''
            SELECT Date, Mode, Category, Amount, income_expense, Currency
            FROM Data 
            WHERE id = %s
            ORDER BY Date DESC
        '''
        df = pd.read_sql_query(query, connection, params=(user_id,))
        connection.close()
        return df
    except Error as e:
        st.error(f"Error fetching user data: {e}")
        return pd.DataFrame()

def get_user_summary(user_id):
    """Get user's financial summary from MySQL database"""
    connection = get_mysql_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Get total income
        cursor.execute('''
            SELECT COALESCE(SUM(Amount), 0) as total_income
            FROM Data 
            WHERE id = %s AND income_expense = 'Income'
        ''', (user_id,))
        total_income = cursor.fetchone()[0]
        
        # Get total expenses
        cursor.execute('''
            SELECT COALESCE(SUM(Amount), 0) as total_expenses
            FROM Data 
            WHERE id = %s AND income_expense = 'Expense'
        ''', (user_id,))
        total_expenses = cursor.fetchone()[0]
        
        # Get transaction count
        cursor.execute('''
            SELECT COUNT(*) as transaction_count
            FROM Data 
            WHERE id = %s
        ''', (user_id,))
        transaction_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_balance': total_income - total_expenses,
            'transaction_count': transaction_count
        }
    except Error as e:
        st.error(f"Error fetching user summary: {e}")
        return None

def get_category_data(user_id):
    """Get expense category breakdown for user"""
    connection = get_mysql_connection()
    if connection is None:
        return pd.DataFrame()
    
    try:
        query = '''
            SELECT Category, SUM(Amount) as TotalAmount
            FROM Data 
            WHERE id = %s AND income_expense = 'Expense'
            GROUP BY Category
            ORDER BY TotalAmount DESC
        '''
        df = pd.read_sql_query(query, connection, params=(user_id,))
        connection.close()
        return df
    except Error as e:
        st.error(f"Error fetching category data: {e}")
        return pd.DataFrame()

def get_monthly_trends(user_id):
    """Get monthly income vs expenses trends"""
    connection = get_mysql_connection()
    if connection is None:
        return pd.DataFrame()
    
    try:
        query = '''
            SELECT 
                DATE_FORMAT(Date, '%Y-%m') as Month,
                income_expense,
                SUM(Amount) as TotalAmount
            FROM Data 
            WHERE id = %s
            GROUP BY DATE_FORMAT(Date, '%Y-%m'), income_expense
            ORDER BY Month
        '''
        df = pd.read_sql_query(query, connection, params=(user_id,))
        connection.close()
        return df
    except Error as e:
        st.error(f"Error fetching monthly trends: {e}")
        return pd.DataFrame()

def get_advanced_analytics_data(user_id):
    """Get comprehensive analytics data for advanced visualizations"""
    connection = get_mysql_connection()
    if connection is None:
        return {}
    
    try:
        cursor = connection.cursor()
        
        # 1. Daily spending patterns
        cursor.execute('''
            SELECT 
                DATE(Date) as Day,
                SUM(CASE WHEN income_expense = 'Expense' THEN Amount ELSE 0 END) as DailyExpense,
                SUM(CASE WHEN income_expense = 'Income' THEN Amount ELSE 0 END) as DailyIncome,
                COUNT(CASE WHEN income_expense = 'Expense' THEN 1 END) as ExpenseCount,
                COUNT(CASE WHEN income_expense = 'Income' THEN 1 END) as IncomeCount
            FROM Data 
            WHERE id = %s
            GROUP BY DATE(Date)
            ORDER BY Day
        ''', (user_id,))
        daily_data = pd.DataFrame(cursor.fetchall(), columns=['Day', 'DailyExpense', 'DailyIncome', 'ExpenseCount', 'IncomeCount'])
        
        # 2. Category-wise spending over time
        cursor.execute('''
            SELECT 
                Category,
                DATE_FORMAT(Date, '%%Y-%%m') as Month,
                SUM(Amount) as TotalAmount,
                COUNT(*) as TransactionCount
            FROM Data 
            WHERE id = %s AND income_expense = 'Expense'
            GROUP BY Category, DATE_FORMAT(Date, '%%Y-%%m')
            ORDER BY Month, TotalAmount DESC
        ''', (user_id,))
        category_trends = pd.DataFrame(cursor.fetchall(), columns=['Category', 'Month', 'TotalAmount', 'TransactionCount'])
        
        # 3. Payment method analysis
        cursor.execute('''
            SELECT 
                Mode,
                COUNT(*) as TransactionCount,
                SUM(Amount) as TotalAmount,
                AVG(Amount) as AvgAmount,
                MIN(Amount) as MinAmount,
                MAX(Amount) as MaxAmount
            FROM Data 
            WHERE id = %s
            GROUP BY Mode
            ORDER BY TotalAmount DESC
        ''', (user_id,))
        payment_analysis = pd.DataFrame(cursor.fetchall(), columns=['Mode', 'TransactionCount', 'TotalAmount', 'AvgAmount', 'MinAmount', 'MaxAmount'])
        
        # 4. Weekly spending patterns
        cursor.execute('''
            SELECT 
                DAYOFWEEK(Date) as DayOfWeek,
                DAYNAME(Date) as DayName,
                SUM(CASE WHEN income_expense = 'Expense' THEN Amount ELSE 0 END) as WeeklyExpense,
                COUNT(CASE WHEN income_expense = 'Expense' THEN 1 END) as ExpenseCount
            FROM Data 
            WHERE id = %s
            GROUP BY DAYOFWEEK(Date), DAYNAME(Date)
            ORDER BY DAYOFWEEK(Date)
        ''', (user_id,))
        weekly_patterns = pd.DataFrame(cursor.fetchall(), columns=['DayOfWeek', 'DayName', 'WeeklyExpense', 'ExpenseCount'])
        
        # 5. Top spending categories by month
        cursor.execute('''
            SELECT 
                Category,
                DATE_FORMAT(Date, '%%Y-%%m') as Month,
                SUM(Amount) as TotalAmount
            FROM Data 
            WHERE id = %s AND income_expense = 'Expense'
            GROUP BY Category, DATE_FORMAT(Date, '%%Y-%%m')
            HAVING TotalAmount > 0
            ORDER BY Month, TotalAmount DESC
        ''', (user_id,))
        top_categories = pd.DataFrame(cursor.fetchall(), columns=['Category', 'Month', 'TotalAmount'])
        
        # 6. Income vs Expense ratio by month
        cursor.execute('''
            SELECT 
                DATE_FORMAT(Date, '%%Y-%%m') as Month,
                SUM(CASE WHEN income_expense = 'Income' THEN Amount ELSE 0 END) as TotalIncome,
                SUM(CASE WHEN income_expense = 'Expense' THEN Amount ELSE 0 END) as TotalExpense,
                (SUM(CASE WHEN income_expense = 'Income' THEN Amount ELSE 0 END) - 
                 SUM(CASE WHEN income_expense = 'Expense' THEN Amount ELSE 0 END)) as NetAmount
            FROM Data 
            WHERE id = %s
            GROUP BY DATE_FORMAT(Date, '%%Y-%%m')
            ORDER BY Month
        ''', (user_id,))
        monthly_ratio = pd.DataFrame(cursor.fetchall(), columns=['Month', 'TotalIncome', 'TotalExpense', 'NetAmount'])
        
        cursor.close()
        connection.close()
        
        # Convert numeric columns to proper data types
        if not daily_data.empty:
            daily_data['DailyExpense'] = pd.to_numeric(daily_data['DailyExpense'], errors='coerce')
            daily_data['DailyIncome'] = pd.to_numeric(daily_data['DailyIncome'], errors='coerce')
            daily_data['ExpenseCount'] = pd.to_numeric(daily_data['ExpenseCount'], errors='coerce')
            daily_data['IncomeCount'] = pd.to_numeric(daily_data['IncomeCount'], errors='coerce')
        
        if not category_trends.empty:
            category_trends['TotalAmount'] = pd.to_numeric(category_trends['TotalAmount'], errors='coerce')
            category_trends['TransactionCount'] = pd.to_numeric(category_trends['TransactionCount'], errors='coerce')
        
        if not payment_analysis.empty:
            payment_analysis['TotalAmount'] = pd.to_numeric(payment_analysis['TotalAmount'], errors='coerce')
            payment_analysis['AvgAmount'] = pd.to_numeric(payment_analysis['AvgAmount'], errors='coerce')
            payment_analysis['MinAmount'] = pd.to_numeric(payment_analysis['MinAmount'], errors='coerce')
            payment_analysis['MaxAmount'] = pd.to_numeric(payment_analysis['MaxAmount'], errors='coerce')
            payment_analysis['TransactionCount'] = pd.to_numeric(payment_analysis['TransactionCount'], errors='coerce')
        
        if not weekly_patterns.empty:
            weekly_patterns['WeeklyExpense'] = pd.to_numeric(weekly_patterns['WeeklyExpense'], errors='coerce')
            weekly_patterns['ExpenseCount'] = pd.to_numeric(weekly_patterns['ExpenseCount'], errors='coerce')
        
        if not top_categories.empty:
            top_categories['TotalAmount'] = pd.to_numeric(top_categories['TotalAmount'], errors='coerce')
        
        if not monthly_ratio.empty:
            monthly_ratio['TotalIncome'] = pd.to_numeric(monthly_ratio['TotalIncome'], errors='coerce')
            monthly_ratio['TotalExpense'] = pd.to_numeric(monthly_ratio['TotalExpense'], errors='coerce')
            monthly_ratio['NetAmount'] = pd.to_numeric(monthly_ratio['NetAmount'], errors='coerce')
        
        return {
            'daily_data': daily_data,
            'category_trends': category_trends,
            'payment_analysis': payment_analysis,
            'weekly_patterns': weekly_patterns,
            'top_categories': top_categories,
            'monthly_ratio': monthly_ratio
        }
    except Error as e:
        st.error(f"Error fetching advanced analytics: {e}")
        return {}

def advanced_analytics_page():
    """Display advanced analytics page with comprehensive spending trends"""
    st.markdown(f'<h1 class="main-header">📊 Advanced Analytics - {st.session_state.user_name}</h1>', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.rerun()
    
    # Get advanced analytics data
    analytics_data = get_advanced_analytics_data(st.session_state.user_id)
    
    if not analytics_data:
        st.error("❌ Unable to load analytics data. Please try again.")
        return
    
    # 1. Daily Spending Trends
    st.markdown("### 📈 Daily Spending Patterns")
    daily_data = analytics_data['daily_data']
    if not daily_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_data['Day'], 
                y=daily_data['DailyExpense'], 
                name='Daily Expenses',
                line=dict(color='red'),
                mode='lines+markers'
            ))
            fig.add_trace(go.Scatter(
                x=daily_data['Day'], 
                y=daily_data['DailyIncome'], 
                name='Daily Income',
                line=dict(color='green'),
                mode='lines+markers'
            ))
            fig.update_layout(
                title="Daily Income vs Expenses",
                xaxis_title="Date",
                yaxis_title="Amount (₹)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=daily_data['Day'],
                y=daily_data['ExpenseCount'],
                name='Expense Transactions',
                marker_color='red'
            ))
            fig.add_trace(go.Bar(
                x=daily_data['Day'],
                y=daily_data['IncomeCount'],
                name='Income Transactions',
                marker_color='green'
            ))
            fig.update_layout(
                title="Daily Transaction Count",
                xaxis_title="Date",
                yaxis_title="Number of Transactions",
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 2. Category Spending Trends Over Time
    st.markdown("### 🏷️ Category Spending Trends")
    category_trends = analytics_data['category_trends']
    if not category_trends.empty:
        # Pivot data for heatmap
        pivot_data = category_trends.pivot(index='Category', columns='Month', values='TotalAmount').fillna(0)
        
        fig = px.imshow(
            pivot_data,
            title="Category Spending Heatmap",
            labels=dict(x="Month", y="Category", color="Amount (₹)"),
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top categories line chart - Fixed the nlargest issue
        try:
            category_sums = category_trends.groupby('Category')['TotalAmount'].sum()
            top_categories = category_sums.nlargest(5)
            top_cat_data = category_trends[category_trends['Category'].isin(top_categories.index)]
            
            fig = px.line(
                top_cat_data,
                x='Month',
                y='TotalAmount',
                color='Category',
                title="Top 5 Categories - Monthly Trends"
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate top categories chart: {e}")
    
    # 3. Payment Method Analysis
    st.markdown("### 💳 Payment Method Analysis")
    payment_analysis = analytics_data['payment_analysis']
    if not payment_analysis.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                payment_analysis,
                values='TotalAmount',
                names='Mode',
                title="Total Amount by Payment Method"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                payment_analysis,
                x='Mode',
                y='AvgAmount',
                title="Average Transaction Amount by Payment Method",
                color='TransactionCount',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 4. Weekly Spending Patterns
    st.markdown("### 📅 Weekly Spending Patterns")
    weekly_patterns = analytics_data['weekly_patterns']
    if not weekly_patterns.empty:
        fig = px.bar(
            weekly_patterns,
            x='DayName',
            y='WeeklyExpense',
            title="Average Spending by Day of Week",
            color='ExpenseCount',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 5. Monthly Income vs Expense Ratio
    st.markdown("### 💰 Monthly Financial Health")
    monthly_ratio = analytics_data['monthly_ratio']
    if not monthly_ratio.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=monthly_ratio['Month'],
                y=monthly_ratio['TotalIncome'],
                name='Income',
                marker_color='green'
            ))
            fig.add_trace(go.Bar(
                x=monthly_ratio['Month'],
                y=monthly_ratio['TotalExpense'],
                name='Expenses',
                marker_color='red'
            ))
            fig.update_layout(
                title="Monthly Income vs Expenses",
                xaxis_title="Month",
                yaxis_title="Amount (₹)",
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Calculate savings rate
            monthly_ratio['SavingsRate'] = (monthly_ratio['NetAmount'] / monthly_ratio['TotalIncome'] * 100).fillna(0)
            
            fig = px.line(
                monthly_ratio,
                x='Month',
                y='SavingsRate',
                title="Monthly Savings Rate (%)",
                markers=True
            )
            fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Break-even")
            st.plotly_chart(fig, use_container_width=True)
    
    # 6. Spending Insights
    st.markdown("### 💡 Spending Insights")
    
    if not daily_data.empty and not category_trends.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Highest spending day
            try:
                max_expense_day = daily_data.loc[daily_data['DailyExpense'].idxmax()]
                st.metric(
                    "Highest Spending Day",
                    f"₹{max_expense_day['DailyExpense']:,.0f}",
                    f"on {max_expense_day['Day']}"
                )
            except Exception as e:
                st.metric("Highest Spending Day", "N/A")
        
        with col2:
            # Most frequent category
            try:
                top_category = category_trends.groupby('Category')['TransactionCount'].sum().idxmax()
                st.metric(
                    "Most Frequent Category",
                    top_category
                )
            except Exception as e:
                st.metric("Most Frequent Category", "N/A")
        
        with col3:
            # Average daily spending
            try:
                avg_daily_expense = daily_data['DailyExpense'].mean()
                st.metric(
                    "Average Daily Spending",
                    f"₹{avg_daily_expense:,.0f}"
                )
            except Exception as e:
                st.metric("Average Daily Spending", "N/A")
    
    # 7. Detailed Statistics Table
    st.markdown("### 📊 Detailed Statistics")
    
    if not payment_analysis.empty:
        st.dataframe(
            payment_analysis,
            use_container_width=True,
            column_config={
                "TotalAmount": st.column_config.NumberColumn("Total Amount (₹)", format="₹%.2f"),
                "AvgAmount": st.column_config.NumberColumn("Average Amount (₹)", format="₹%.2f"),
                "MinAmount": st.column_config.NumberColumn("Min Amount (₹)", format="₹%.2f"),
                "MaxAmount": st.column_config.NumberColumn("Max Amount (₹)", format="₹%.2f")
            }
        )

def login_page():
    """Display login page"""
    st.markdown('<h1 class="main-header">💰 Dabba Expense Tracker</h1>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown("### 🔐 Login to Your Account")
        
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="Enter your email")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit_button = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit_button:
                if email and password:
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user[0]
                        st.session_state.user_name = user[1]
                        st.success("✅ Login successful! Welcome back!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password. Please try again.")
                else:
                    st.error("❌ Please fill in all fields.")
        
        st.markdown("---")
        st.markdown("### 📋 Demo Accounts")
        st.markdown("You can use any of these accounts to test the application:")
        
        demo_accounts = [
            ("himnish@gmail.com", "himnish@123"),
            ("rishi@gmail.com", "rishi@123"),
            ("surya@gmail.com", "surya@123"),
            ("sandeep@gmail.com", "sandeep@123"),
            ("shaura@gmail.com", "shaura@123")
        ]
        
        for email, password in demo_accounts:
            st.code(f"Email: {email} | Password: {password}")
        
        st.markdown("</div>", unsafe_allow_html=True)

def dashboard():
    """Display main dashboard after login"""
    st.markdown(f'<h1 class="main-header">💰 Welcome, {st.session_state.user_name}! 👋</h1>', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("📊 Advanced Analytics"):
            st.session_state.current_page = "analytics"
            st.rerun()
    with col2:
        if st.button("🤖 AI Chatbot"):
            st.session_state.current_page = "chatbot"
            st.rerun()
    with col4:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.rerun()
    
    # Get user data and summary
    user_data = get_user_data(st.session_state.user_id)
    user_summary = get_user_summary(st.session_state.user_id)
    
    if user_data.empty:
        st.warning("📊 No transaction data found for this user.")
        st.info("💡 This user doesn't have any transactions in the database yet.")
        return
    
    if user_summary is None:
        st.error("❌ Error loading user data. Please try again.")
        return
    
    # Display financial overview
    st.markdown("### 📊 Your Financial Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Income", f"₹{user_summary['total_income']:,.0f}")
    with col2:
        st.metric("💸 Total Expenses", f"₹{user_summary['total_expenses']:,.0f}")
    with col3:
        st.metric("📊 Net Balance", f"₹{user_summary['net_balance']:,.0f}")
    with col4:
        st.metric("📅 Total Transactions", user_summary['transaction_count'])
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Expense Categories")
        category_data = get_category_data(st.session_state.user_id)
        if not category_data.empty:
            fig = px.pie(
                values=category_data['TotalAmount'], 
                names=category_data['Category'], 
                title="Expense Distribution by Category"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data available for categories chart.")
    
    with col2:
        st.markdown("### 📈 Monthly Income vs Expenses")
        monthly_data = get_monthly_trends(st.session_state.user_id)
        if not monthly_data.empty:
            # Pivot the data for better visualization
            pivot_data = monthly_data.pivot(index='Month', columns='income_expense', values='TotalAmount').fillna(0)
            
            fig = go.Figure()
            if 'Income' in pivot_data.columns:
                fig.add_trace(go.Scatter(
                    x=pivot_data.index, 
                    y=pivot_data['Income'], 
                    name='Income', 
                    line=dict(color='green'),
                    mode='lines+markers'
                ))
            if 'Expense' in pivot_data.columns:
                fig.add_trace(go.Scatter(
                    x=pivot_data.index, 
                    y=pivot_data['Expense'], 
                    name='Expenses', 
                    line=dict(color='red'),
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title="Monthly Income vs Expenses Trend",
                xaxis_title="Month",
                yaxis_title="Amount (₹)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No monthly trend data available.")
    
    # Recent transactions
    st.markdown("### 📋 Recent Transactions")
    st.dataframe(
        user_data.head(20), 
        use_container_width=True,
        column_config={
            "Date": st.column_config.DateColumn("Date"),
            "Amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
            "income_expense": st.column_config.SelectboxColumn("Type", options=["Income", "Expense"])
        }
    )
    
    # Transaction statistics
    st.markdown("### 📈 Transaction Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Transaction Summary**")
        income_count = len(user_data[user_data['income_expense'] == 'Income'])
        expense_count = len(user_data[user_data['income_expense'] == 'Expense'])
        
        st.metric("Income Transactions", income_count)
        st.metric("Expense Transactions", expense_count)
        
        if not user_data.empty:
            avg_income = user_data[user_data['income_expense'] == 'Income']['Amount'].mean()
            avg_expense = user_data[user_data['income_expense'] == 'Expense']['Amount'].mean()
            
            st.metric("Average Income", f"₹{avg_income:,.2f}")
            st.metric("Average Expense", f"₹{avg_expense:,.2f}")
    
    with col2:
        st.markdown("**Payment Methods**")
        payment_methods = user_data['Mode'].value_counts()
        if not payment_methods.empty:
            fig = px.bar(
                x=payment_methods.index, 
                y=payment_methods.values,
                title="Transactions by Payment Method"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No payment method data available.")

# Grok AI API Configuration
GROK_API_KEY = st.secrets.get("GROK_API_KEY", "your-grok-api-key-here")
GROK_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_grok_api(user_query, context_data):
    """Call Grok AI API with user query and context data"""
    try:
        # Prepare the context with user data
        context = f"""
        You are a financial advisor chatbot for the Dabba expense tracker app. 
        You have access to the following user data:
        
        User Summary:
        - Total Income: ₹{context_data.get('total_income', 0):,.0f}
        - Total Expenses: ₹{context_data.get('total_expenses', 0):,.0f}
        - Net Balance: ₹{context_data.get('net_balance', 0):,.0f}
        - Total Transactions: {context_data.get('transaction_count', 0)}
        
        Category Breakdown:
        {context_data.get('category_data', pd.DataFrame()).to_string() if not context_data.get('category_data', pd.DataFrame()).empty else 'No category data available'}
        
        Recent Transactions:
        {context_data.get('recent_data', pd.DataFrame()).to_string() if not context_data.get('recent_data', pd.DataFrame()).empty else 'No recent transactions'}
        
        Payment Methods:
        {context_data.get('payment_data', pd.DataFrame()).to_string() if not context_data.get('payment_data', pd.DataFrame()).empty else 'No payment data available'}
        
        User Query: {user_query}
        
        Please provide a helpful, personalized response based on the user's financial data. 
        Be conversational, provide insights, and suggest improvements where appropriate.
        Only use the user's own data - do not reference other users' data.
        """
        
        headers = {
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful financial advisor chatbot for the Dabba expense tracker app. Provide personalized financial insights and advice based on the user's data."
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(GROK_API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            st.error(f"Error calling Grok API: {response.status_code} - {response.text}")
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
            
    except Exception as e:
        st.error(f"Error calling Grok API: {e}")
        return "I'm sorry, I'm experiencing technical difficulties. Please try again later."

def get_analytics_data_for_chatbot(user_id):
    """Get comprehensive analytics data for the chatbot"""
    connection = get_mysql_connection()
    if connection is None:
        return {}
    
    try:
        cursor = connection.cursor()
        
        # Category breakdown
        cursor.execute('''
            SELECT Category, SUM(Amount) as TotalAmount, COUNT(*) as TransactionCount
            FROM Data 
            WHERE id = %s AND income_expense = 'Expense'
            GROUP BY Category
            ORDER BY TotalAmount DESC
        ''', (user_id,))
        category_data = pd.DataFrame(cursor.fetchall(), columns=['Category', 'TotalAmount', 'TransactionCount'])
        
        # Monthly trends
        cursor.execute('''
            SELECT 
                DATE_FORMAT(Date, '%Y-%m') as Month,
                income_expense,
                SUM(Amount) as TotalAmount
            FROM Data 
            WHERE id = %s
            GROUP BY DATE_FORMAT(Date, '%Y-%m'), income_expense
            ORDER BY Month
        ''', (user_id,))
        monthly_data = pd.DataFrame(cursor.fetchall(), columns=['Month', 'income_expense', 'TotalAmount'])
        
        # Payment methods
        cursor.execute('''
            SELECT Mode, COUNT(*) as TransactionCount, SUM(Amount) as TotalAmount
            FROM Data 
            WHERE id = %s
            GROUP BY Mode
            ORDER BY TotalAmount DESC
        ''', (user_id,))
        payment_data = pd.DataFrame(cursor.fetchall(), columns=['Mode', 'TransactionCount', 'TotalAmount'])
        
        # Recent transactions
        cursor.execute('''
            SELECT Date, Category, Amount, income_expense, Mode
            FROM Data 
            WHERE id = %s
            ORDER BY Date DESC
            LIMIT 10
        ''', (user_id,))
        recent_data = pd.DataFrame(cursor.fetchall(), columns=['Date', 'Category', 'Amount', 'income_expense', 'Mode'])
        
        cursor.close()
        connection.close()
        
        return {
            'category_data': category_data,
            'monthly_data': monthly_data,
            'payment_data': payment_data,
            'recent_data': recent_data
        }
    except Error as e:
        st.error(f"Error fetching analytics data: {e}")
        return {}

def chatbot_page():
    """Display the chatbot interface"""
    st.markdown('<h1 class="main-header">🤖 Dabba Financial Advisor Chatbot</h1>', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()
    with col2:
        if st.button("📊 Advanced Analytics"):
            st.session_state.current_page = "analytics"
            st.rerun()
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.rerun()
    
    # Get user data
    user_id = st.session_state.get('user_id')
    user_name = st.session_state.get('user_name')
    
    if not user_id:
        st.error("User ID not found. Please login again.")
        return
    
    # Get user summary and analytics data
    user_summary = get_user_summary(user_id)
    analytics_data = get_analytics_data_for_chatbot(user_id)
    
    if user_summary is None:
        st.error("Unable to load user data. Please try again.")
        return
    
    # Display user info
    st.markdown(f"### 👤 Welcome, {user_name}!")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Income", f"₹{user_summary['total_income']:,.0f}")
    with col2:
        st.metric("💸 Total Expenses", f"₹{user_summary['total_expenses']:,.0f}")
    with col3:
        st.metric("📊 Net Balance", f"₹{user_summary['net_balance']:,.0f}")
    with col4:
        st.metric("📅 Transactions", user_summary['transaction_count'])
    
    # Chatbot interface
    st.markdown("### 💬 Ask me anything about your finances!")
    
    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**🤖 Financial Advisor:** {message['content']}")
    
    # User input
    user_input = st.text_input("Ask me about your spending patterns, savings, or financial advice:", key="user_input")
    
    if st.button("Send", key="send_button") and user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        # Prepare context data
        context_data = {
            'total_income': user_summary['total_income'],
            'total_expenses': user_summary['total_expenses'],
            'net_balance': user_summary['net_balance'],
            'transaction_count': user_summary['transaction_count'],
            'category_data': analytics_data.get('category_data', pd.DataFrame()),
            'recent_data': analytics_data.get('recent_data', pd.DataFrame()),
            'payment_data': analytics_data.get('payment_data', pd.DataFrame())
        }
        
        # Show loading message
        with st.spinner("🤖 Analyzing your financial data..."):
            # Call Grok API
            response = call_grok_api(user_input, context_data)
            
            # Add bot response to chat history
            st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        
        # Clear the input field by rerunning
        st.rerun()
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Suggested questions
    st.markdown("### 💡 Suggested Questions:")
    suggested_questions = [
        "What are my biggest spending categories?",
        "How can I improve my savings?",
        "What's my spending trend over the last few months?",
        "Which payment method do I use most?",
        "What are my recent transactions?",
        "How does my income compare to my expenses?",
        "What financial advice do you have for me?",
        "How can I reduce my expenses?"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(suggested_questions):
        with cols[i % 2]:
            if st.button(question, key=f"suggest_{i}"):
                # Add the question directly to chat history and process it
                st.session_state.chat_history.append({'role': 'user', 'content': question})
                
                # Prepare context data
                context_data = {
                    'total_income': user_summary['total_income'],
                    'total_expenses': user_summary['total_expenses'],
                    'net_balance': user_summary['net_balance'],
                    'transaction_count': user_summary['transaction_count'],
                    'category_data': analytics_data.get('category_data', pd.DataFrame()),
                    'recent_data': analytics_data.get('recent_data', pd.DataFrame()),
                    'payment_data': analytics_data.get('payment_data', pd.DataFrame())
                }
                
                # Show loading message and get response
                with st.spinner("🤖 Analyzing your financial data..."):
                    response = call_grok_api(question, context_data)
                    st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                
                st.rerun()
    
    # Display some quick insights
    if analytics_data.get('category_data') is not None and not analytics_data['category_data'].empty:
        st.markdown("### 📊 Quick Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top spending category
            top_category = analytics_data['category_data'].iloc[0]
            st.metric(
                "🏆 Top Spending Category",
                top_category['Category'],
                f"₹{top_category['TotalAmount']:,.0f}"
            )
        
        with col2:
            # Most used payment method
            if not analytics_data['payment_data'].empty:
                top_payment = analytics_data['payment_data'].iloc[0]
                st.metric(
                    "💳 Most Used Payment Method",
                    top_payment['Mode'],
                    f"{top_payment['TransactionCount']} transactions"
                )

def main():
    """Main application function"""
    # Initialize current page in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    if not st.session_state.authenticated:
        login_page()
    else:
        if st.session_state.current_page == "analytics":
            advanced_analytics_page()
        elif st.session_state.current_page == "chatbot":
            chatbot_page()
        else:
            dashboard()

if __name__ == "__main__":
    main()
