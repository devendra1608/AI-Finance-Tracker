import streamlit as st
import mysql.connector
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Grok AI API Configuration
GROK_API_KEY = st.secrets.get("GROK_API_KEY", "your-grok-api-key-here")
GROK_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_mysql_connection():
    """Create MySQL connection to XAMPP database"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='dabba',
            user='root',
            password=''
        )
        return connection
    except Exception as e:
        st.error(f"Error connecting to MySQL database: {e}")
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
    except Exception as e:
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
    except Exception as e:
        st.error(f"Error fetching user summary: {e}")
        return None

def get_analytics_data(user_id):
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
    except Exception as e:
        st.error(f"Error fetching analytics data: {e}")
        return {}

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
            "model": "llama-3-70b-8192",
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

def chatbot_page():
    """Display the chatbot interface"""
    st.markdown('<h1 class="main-header">🤖 Dabba Financial Advisor Chatbot</h1>', unsafe_allow_html=True)
    
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
    
    # Check if user is authenticated
    if not st.session_state.get('authenticated', False):
        st.error("Please login first to access the chatbot.")
        return
    
    # Get user data
    user_id = st.session_state.get('user_id')
    user_name = st.session_state.get('user_name')
    
    if not user_id:
        st.error("User ID not found. Please login again.")
        return
    
    # Get user summary and analytics data
    user_summary = get_user_summary(user_id)
    analytics_data = get_analytics_data(user_id)
    
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
        
        # Rerun to update the display
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
                st.session_state.user_input = question
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
    """Main function to run the chatbot"""
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "chatbot"
    
    # Page configuration
    st.set_page_config(
        page_title="Dabba - Financial Advisor Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            color: #1f77b4;
            margin-bottom: 2rem;
        }
        .chat-message {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 10px;
        }
        .user-message {
            background-color: #e3f2fd;
            text-align: right;
        }
        .bot-message {
            background-color: #f5f5f5;
            text-align: left;
        }
    </style>
    """, unsafe_allow_html=True)
    
    chatbot_page()

if __name__ == "__main__":
    main() 