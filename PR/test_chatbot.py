#!/usr/bin/env python3
"""
Test script for the Dabba Chatbot functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mysql.connector
import pandas as pd
import requests
import json

def test_database_connection():
    """Test database connection"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='dabba',
            user='root',
            password=''
        )
        print("✅ Database connection successful")
        
        # Test query
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Found {user_count} users in database")
        
        cursor.execute("SELECT COUNT(*) FROM Data")
        data_count = cursor.fetchone()[0]
        print(f"✅ Found {data_count} transactions in database")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_data_retrieval():
    """Test user data retrieval"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='dabba',
            user='root',
            password=''
        )
        
        # Test user 1 data
        query = '''
            SELECT Date, Mode, Category, Amount, income_expense, Currency
            FROM Data 
            WHERE id = 1
            ORDER BY Date DESC
            LIMIT 5
        '''
        df = pd.read_sql_query(query, connection)
        print(f"✅ Retrieved {len(df)} transactions for user 1")
        
        # Test user summary
        cursor = connection.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(Amount), 0) as total_income
            FROM Data 
            WHERE id = 1 AND income_expense = 'Income'
        ''', (1,))
        total_income = cursor.fetchone()[0]
        print(f"✅ User 1 total income: ₹{total_income:,.0f}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ User data retrieval failed: {e}")
        return False

def test_analytics_data():
    """Test analytics data retrieval"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='dabba',
            user='root',
            password=''
        )
        
        cursor = connection.cursor()
        
        # Test category breakdown
        cursor.execute('''
            SELECT Category, SUM(Amount) as TotalAmount, COUNT(*) as TransactionCount
            FROM Data 
            WHERE id = 1 AND income_expense = 'Expense'
            GROUP BY Category
            ORDER BY TotalAmount DESC
            LIMIT 3
        ''', (1,))
        category_data = pd.DataFrame(cursor.fetchall(), columns=['Category', 'TotalAmount', 'TransactionCount'])
        print(f"✅ Retrieved category data: {len(category_data)} categories")
        
        # Test payment methods
        cursor.execute('''
            SELECT Mode, COUNT(*) as TransactionCount, SUM(Amount) as TotalAmount
            FROM Data 
            WHERE id = 1
            GROUP BY Mode
            ORDER BY TotalAmount DESC
        ''', (1,))
        payment_data = pd.DataFrame(cursor.fetchall(), columns=['Mode', 'TransactionCount', 'TotalAmount'])
        print(f"✅ Retrieved payment data: {len(payment_data)} payment methods")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Analytics data retrieval failed: {e}")
        return False

def test_grok_api_simulation():
    """Simulate Grok API call (without actual API key)"""
    try:
        # Simulate context data
        context_data = {
            'total_income': 50000,
            'total_expenses': 30000,
            'net_balance': 20000,
            'transaction_count': 50,
            'category_data': pd.DataFrame({
                'Category': ['Food', 'Transport', 'Shopping'],
                'TotalAmount': [10000, 8000, 12000],
                'TransactionCount': [20, 15, 15]
            }),
            'recent_data': pd.DataFrame({
                'Date': ['2025-01-01', '2025-01-02'],
                'Category': ['Food', 'Transport'],
                'Amount': [500, 300],
                'income_expense': ['Expense', 'Expense'],
                'Mode': ['UPI', 'UPI']
            }),
            'payment_data': pd.DataFrame({
                'Mode': ['UPI', 'Cash'],
                'TransactionCount': [40, 10],
                'TotalAmount': [45000, 5000]
            })
        }
        
        print("✅ Context data prepared successfully")
        print(f"   - Total Income: ₹{context_data['total_income']:,.0f}")
        print(f"   - Total Expenses: ₹{context_data['total_expenses']:,.0f}")
        print(f"   - Net Balance: ₹{context_data['net_balance']:,.0f}")
        print(f"   - Transactions: {context_data['transaction_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Grok API simulation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Dabba Chatbot Functionality")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("User Data Retrieval", test_user_data_retrieval),
        ("Analytics Data", test_analytics_data),
        ("Grok API Simulation", test_grok_api_simulation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The chatbot should work correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    print("\n📝 Next Steps:")
    print("1. Ensure XAMPP is running with MySQL on port 3306")
    print("2. Import dabba.sql into your database")
    print("3. Get a Grok AI API key from https://console.groq.com/")
    print("4. Update the API key in .streamlit/secrets.toml")
    print("5. Run: streamlit run app.py")

if __name__ == "__main__":
    main() 