import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def get_mysql_connection():
    """Create MySQL connection to XAMPP database"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3307,  # Default XAMPP MySQL port
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

def get_available_categories():
    """Get list of available categories from existing data"""
    connection = get_mysql_connection()
    if connection is None:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT DISTINCT Category 
            FROM Data 
            ORDER BY Category
        ''')
        categories = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return categories
    except Error as e:
        st.error(f"Error fetching categories: {e}")
        connection.close()
        return []

def get_available_modes():
    """Get list of available payment modes from existing data"""
    connection = get_mysql_connection()
    if connection is None:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT DISTINCT Mode 
            FROM Data 
            ORDER BY Mode
        ''')
        modes = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return modes
    except Error as e:
        st.error(f"Error fetching payment modes: {e}")
        connection.close()
        return []

def insert_transaction(user_id, date, mode, category, amount, income_expense, currency):
    """Insert a new transaction into the MySQL database"""
    connection = get_mysql_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO Data (id, Date, Mode, Category, Amount, income_expense, Currency)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, date, mode, category, amount, income_expense, currency))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Error as e:
        st.error(f"Error inserting transaction: {e}")
        connection.close()
        return False

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Basic phone number validation"""
    import re
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it's between 10-15 digits
    return 10 <= len(digits_only) <= 15

def get_next_user_id():
    """Get the next available user ID by counting existing users"""
    connection = get_mysql_connection()
    if connection is None:
        return 1
    
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM Users')
        count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        return count + 1
    except Error as e:
        st.error(f"Error getting user count: {e}")
        connection.close()
        return 1

def check_email_exists(email):
    """Check if email already exists in the database"""
    connection = get_mysql_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM Users WHERE email = %s', (email,))
        count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        return count > 0
    except Error as e:
        st.error(f"Error checking email: {e}")
        connection.close()
        return False

def register_user(name, age, email, password, phone_number):
    """Register a new user in the database"""
    connection = get_mysql_connection()
    if connection is None:
        return False
    
    try:
        # Get next user ID
        next_user_id = get_next_user_id()
        
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO Users (user_id, Name, Age, email, password, phone_number)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (next_user_id, name, age, email, password, phone_number))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Error as e:
        st.error(f"Error registering user: {e}")
        connection.close()
        return False 