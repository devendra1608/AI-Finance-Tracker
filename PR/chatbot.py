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
        Provide responses between 2-6 sentences - not too short, not too long.
        
        User Data:
        - Income: ₹{context_data.get('total_income', 0):,.0f}
        - Expenses: ₹{context_data.get('total_expenses', 0):,.0f}
        - Net: ₹{context_data.get('net_balance', 0):,.0f}
        - Transactions: {context_data.get('transaction_count', 0)}
        
        Top Categories: {context_data.get('category_data', pd.DataFrame()).head(3).to_string() if not context_data.get('category_data', pd.DataFrame()).empty else 'None'}
        
        Recent: {context_data.get('recent_data', pd.DataFrame()).head(3).to_string() if not context_data.get('recent_data', pd.DataFrame()).empty else 'None'}
        
        Query: {user_query}
        
        RESPONSE RULES:
        - Keep responses between 2-6 sentences (not too short, not too long)
        - Be DIRECT and TO-THE-POINT
        - Use bullet points for multiple points
        - Focus on actionable advice
        - Use specific numbers from user data
        - Provide context and explanation
        - Include practical suggestions
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
                    "content": "You are a helpful financial advisor. Provide responses between 2-6 sentences - not too short, not too long. Be direct and to-the-point while providing context and practical suggestions. Use bullet points when needed. Focus on actionable insights and specific data from the user's financial records."
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            "temperature": 0.3,  # Lower temperature for more focused responses
            "max_tokens": 500    # Increased max tokens for 2-6 sentence responses
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

def get_quick_response(user_query, context_data):
    """Provide quick template-based responses for common questions"""
    query_lower = user_query.lower()
    
    # Income vs expenses comparison
    if any(word in query_lower for word in ['income', 'expense', 'compare', 'balance']):
        net_balance = context_data.get('net_balance', 0)
        if net_balance > 0:
            return f"✅ You're in good shape! Net balance: ₹{net_balance:,.0f} (Income exceeds expenses). Your financial health is positive, which means you're saving money effectively. Consider investing the surplus for better returns."
        elif net_balance < 0:
            return f"⚠️ Watch your spending! Net balance: ₹{net_balance:,.0f} (Expenses exceed income). You're spending more than you earn, which can lead to financial stress. Focus on reducing expenses in your top spending categories to improve your financial situation."
        else:
            return "📊 Your income and expenses are perfectly balanced. This is a stable financial position, but you might want to consider increasing your income or reducing expenses to build savings. Aim for a positive net balance for better financial security."
    
    # Top spending categories
    elif any(word in query_lower for word in ['category', 'spending', 'biggest', 'top']):
        category_data = context_data.get('category_data', pd.DataFrame())
        if not category_data.empty:
            top_cat = category_data.iloc[0]
            return f"🏆 Top category: {top_cat['Category']} (₹{top_cat['TotalAmount']:,.0f}). This represents your highest spending area, accounting for {top_cat['TransactionCount']} transactions. Consider reviewing this category for potential savings opportunities and setting a budget limit."
        return "📊 No spending data available yet. Start adding transactions to see your spending patterns and get personalized insights. This will help you identify areas where you can optimize your expenses."
    
    # Recent transactions
    elif any(word in query_lower for word in ['recent', 'latest', 'transactions']):
        recent_data = context_data.get('recent_data', pd.DataFrame())
        if not recent_data.empty:
            latest = recent_data.iloc[0]
            return f"📅 Latest: {latest['Category']} - ₹{latest['Amount']:,.0f} ({latest['income_expense']}). Your recent spending shows a {latest['income_expense'].lower()} transaction. Monitor your recent patterns to maintain financial discipline and avoid unnecessary expenses."
        return "📅 No recent transactions found. Add your daily expenses and income to track your financial activity. Regular transaction logging helps you stay aware of your spending habits and financial goals."
    
    # Savings advice
    elif any(word in query_lower for word in ['save', 'savings', 'improve']):
        net_balance = context_data.get('net_balance', 0)
        if net_balance < 0:
            return "💡 Cut expenses in your top spending category to improve savings. Your current spending exceeds income, so prioritize reducing non-essential expenses. Consider creating a budget and tracking every expense to identify areas for improvement."
        else:
            return "💡 Great job! Consider increasing your savings rate. You're already saving money, which is excellent. Look into investment options or emergency funds to make your money work harder for you."
    
    # Payment methods
    elif any(word in query_lower for word in ['payment', 'method', 'mode']):
        payment_data = context_data.get('payment_data', pd.DataFrame())
        if not payment_data.empty:
            top_payment = payment_data.iloc[0]
            return f"💳 Most used: {top_payment['Mode']} ({top_payment['TransactionCount']} transactions). This is your preferred payment method, indicating your comfort with digital transactions. Consider diversifying payment methods for better financial tracking and security."
        return "💳 No payment data available. Start recording your transactions to see which payment methods you use most. This information helps in better financial planning and understanding your spending patterns."
    
    # Return None to use AI response
    return None

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
            # Try quick response first
            quick_response = get_quick_response(user_input, context_data)
            
            if quick_response:
                response = quick_response
            else:
                # Call Grok API for complex questions
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
    st.markdown("### 💡 Quick Questions:")
    suggested_questions = [
        "What's my net balance?",
        "Top spending category?",
        "Recent transactions?",
        "Payment method used most?",
        "How to improve savings?",
        "Income vs expenses?",
        "Financial advice?",
        "Reduce expenses?"
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