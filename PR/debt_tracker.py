import streamlit as st
import pandas as pd
from database import get_mysql_connection
from mysql.connector import Error
from datetime import datetime
import plotly.express as px

def create_debt_tables():
    """Create debt tracking tables if they don't exist"""
    connection = get_mysql_connection()
    if connection is None:
        return
    
    try:
        cursor = connection.cursor()
        
        # Create Debts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Debts (
                debt_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                debt_name VARCHAR(255) NOT NULL,
                lender_name VARCHAR(255) NOT NULL,
                original_amount DECIMAL(15,2) NOT NULL,
                current_balance DECIMAL(15,2) NOT NULL,
                interest_rate DECIMAL(5,2) NOT NULL,
                interest_type ENUM('Simple', 'Compound') DEFAULT 'Simple',
                payment_frequency ENUM('Monthly', 'Weekly', 'Daily') DEFAULT 'Monthly',
                start_date DATE NOT NULL,
                due_date DATE,
                minimum_payment DECIMAL(15,2) DEFAULT 0,
                debt_priority ENUM('High', 'Medium', 'Low') DEFAULT 'Medium',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        ''')
        
        # Create Debt_Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Debt_Payments (
                payment_id INT AUTO_INCREMENT PRIMARY KEY,
                debt_id INT NOT NULL,
                user_id INT NOT NULL,
                payment_amount DECIMAL(15,2) NOT NULL,
                payment_date DATE NOT NULL,
                payment_type ENUM('Regular', 'Extra', 'Lump Sum') DEFAULT 'Regular',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (debt_id) REFERENCES Debts(debt_id),
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        ''')
        
        connection.commit()
        cursor.close()
        connection.close()
        
    except Exception as e:
        st.error(f"Error creating debt tables: {e}")

def add_debt(user_id, debt_name, lender_name, original_amount, current_balance, 
              interest_rate, interest_type, payment_frequency, start_date, due_date, 
              minimum_payment, debt_priority, notes):
    """Add a new debt for a user"""
    connection = get_mysql_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Convert data types to ensure compatibility with MySQL
        user_id = int(user_id)
        original_amount = float(original_amount)
        current_balance = float(current_balance)
        interest_rate = float(interest_rate)
        minimum_payment = float(minimum_payment) if minimum_payment else 0.0
        
        cursor.execute('''
            INSERT INTO Debts (user_id, debt_name, lender_name, original_amount, 
                              current_balance, interest_rate, interest_type, payment_frequency,
                              start_date, due_date, minimum_payment, debt_priority, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, debt_name, lender_name, original_amount, current_balance,
              interest_rate, interest_type, payment_frequency, start_date, due_date,
              minimum_payment, debt_priority, notes))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        st.error(f"Error adding debt: {e}")
        return False

def get_user_debts(user_id):
    """Get all debts for a user"""
    connection = get_mysql_connection()
    if connection is None:
        return pd.DataFrame()
    
    try:
        query = '''
            SELECT debt_id, debt_name, lender_name, original_amount, current_balance,
                   interest_rate, interest_type, payment_frequency, start_date, due_date,
                   minimum_payment, debt_priority, notes,
                   DATEDIFF(due_date, CURDATE()) as days_remaining
            FROM Debts 
            WHERE user_id = %s AND current_balance > 0
            ORDER BY debt_priority DESC, interest_rate DESC
        '''
        df = pd.read_sql_query(query, connection, params=(user_id,))
        connection.close()
        return df
    except Exception as e:
        st.error(f"Error fetching debts: {e}")
        return pd.DataFrame()

def add_debt_payment(user_id, debt_id, payment_amount, payment_date, payment_type, notes):
    """Add a debt payment"""
    connection = get_mysql_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Convert data types to ensure compatibility with MySQL
        debt_id = int(debt_id)
        user_id = int(user_id)
        payment_amount = float(payment_amount)
        
        # Add payment record
        cursor.execute('''
            INSERT INTO Debt_Payments (debt_id, user_id, payment_amount, payment_date, 
                                      payment_type, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (debt_id, user_id, payment_amount, payment_date, payment_type, notes))
        
        # Update debt balance
        cursor.execute('''
            UPDATE Debts 
            SET current_balance = GREATEST(0, current_balance - %s)
            WHERE debt_id = %s AND user_id = %s
        ''', (payment_amount, debt_id, user_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        st.error(f"Error adding debt payment: {e}")
        return False

def get_debt_payments(user_id, debt_id=None):
    """Get debt payments for a user"""
    connection = get_mysql_connection()
    if connection is None:
        return pd.DataFrame()
    
    try:
        if debt_id:
            query = '''
                SELECT dp.payment_id, dp.payment_amount, dp.payment_date, dp.payment_type,
                       dp.notes, d.debt_name, d.lender_name
                FROM Debt_Payments dp
                JOIN Debts d ON dp.debt_id = d.debt_id
                WHERE dp.user_id = %s AND dp.debt_id = %s
                ORDER BY dp.payment_date DESC
            '''
            df = pd.read_sql_query(query, connection, params=(user_id, debt_id))
        else:
            query = '''
                SELECT dp.payment_id, dp.payment_amount, dp.payment_date, dp.payment_type,
                       dp.notes, d.debt_name, d.lender_name
                FROM Debt_Payments dp
                JOIN Debts d ON dp.debt_id = d.debt_id
                WHERE dp.user_id = %s
                ORDER BY dp.payment_date DESC
            '''
            df = pd.read_sql_query(query, connection, params=(user_id,))
        
        connection.close()
        return df
    except Exception as e:
        st.error(f"Error fetching debt payments: {e}")
        return pd.DataFrame()

def calculate_optimal_repayment_strategy(user_id):
    """Calculate optimal debt repayment strategy using debt avalanche method"""
    debts_df = get_user_debts(user_id)
    if debts_df.empty:
        return None
    
    # Calculate additional metrics for each debt
    debts_df['monthly_interest'] = debts_df['current_balance'] * debts_df['interest_rate'] / 100 / 12
    debts_df['total_interest_paid'] = debts_df['original_amount'] - debts_df['current_balance']
    debts_df['remaining_principal'] = debts_df['current_balance']
    
    # Sort by interest rate (highest first) for avalanche method
    debts_df = debts_df.sort_values('interest_rate', ascending=False)
    
    # Calculate total monthly payments
    total_minimum_payment = debts_df['minimum_payment'].sum()
    
    # Calculate optimal strategy
    strategy = {
        'debts': debts_df.to_dict('records'),
        'total_debt': debts_df['current_balance'].sum(),
        'total_monthly_payment': total_minimum_payment,
        'highest_interest_debt': debts_df.iloc[0] if not debts_df.empty else None,
        'priority_order': debts_df[['debt_name', 'lender_name', 'interest_rate', 'current_balance']].to_dict('records')
    }
    
    return strategy

def calculate_debt_snowball_strategy(user_id):
    """Calculate debt snowball strategy (lowest balance first)"""
    debts_df = get_user_debts(user_id)
    if debts_df.empty:
        return None
    
    # Sort by current balance (lowest first) for snowball method
    debts_df = debts_df.sort_values('current_balance', ascending=True)
    
    strategy = {
        'debts': debts_df.to_dict('records'),
        'total_debt': debts_df['current_balance'].sum(),
        'lowest_balance_debt': debts_df.iloc[0] if not debts_df.empty else None,
        'priority_order': debts_df[['debt_name', 'lender_name', 'current_balance', 'interest_rate']].to_dict('records')
    }
    
    return strategy

def debt_tracker_page():
    """Display the debt tracker interface"""
    st.markdown('<h1 class="main-header"> Debt Tracker</h1>', unsafe_allow_html=True)
    
    
    # Check if user is authenticated
    if not st.session_state.get('authenticated', False):
        st.error("Please login first to access the debt tracker.")
        return
    
    user_id = st.session_state.get('user_id')
    user_name = st.session_state.get('user_name')
    
    if not user_id:
        st.error("User ID not found. Please login again.")
        return
    
    # Create debt tables if they don't exist
    create_debt_tables()
    
    # Get user debts
    debts_df = get_user_debts(user_id)
    
    # Tabs for different debt management features
    tab1, tab2, tab3, tab4 = st.tabs([" Debt Overview", " Add Debt", " Make Payment", " Repayment Strategy"])
    
    with tab1:
        st.markdown("###  Your Debt Overview")
        
        if debts_df.empty:
            st.info(" You have no active debts! Great job managing your finances.")
        else:
            # Debt summary metrics
            total_debt = debts_df['current_balance'].sum()
            total_original = debts_df['original_amount'].sum()
            total_paid = total_original - total_debt
            avg_interest = debts_df['interest_rate'].mean()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(" Total Debt", f"₹{total_debt:,.0f}")
            with col2:
                st.metric(" Original Amount", f"₹{total_original:,.0f}")
            with col3:
                st.metric(" Amount Paid", f"₹{total_paid:,.0f}")
            with col4:
                st.metric(" Avg Interest Rate", f"{avg_interest:.1f}%")
            
            # Display debts table
            st.markdown("###  Your Debts")
            
            # Format the dataframe for display
            display_df = debts_df.copy()
            display_df['current_balance'] = display_df['current_balance'].apply(lambda x: f"₹{x:,.0f}")
            display_df['original_amount'] = display_df['original_amount'].apply(lambda x: f"₹{x:,.0f}")
            display_df['interest_rate'] = display_df['interest_rate'].apply(lambda x: f"{x:.1f}%")
            display_df['days_remaining'] = display_df['days_remaining'].apply(lambda x: f"{x} days" if x > 0 else "Overdue" if x < 0 else "Due today")
            
            # Select columns to display
            display_columns = ['debt_name', 'lender_name', 'current_balance', 'interest_rate', 
                             'payment_frequency', 'debt_priority', 'days_remaining']
            
            st.dataframe(display_df[display_columns], use_container_width=True)
            
            # Debt charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Debt by priority
                priority_data = debts_df.groupby('debt_priority')['current_balance'].sum()
                if not priority_data.empty:
                    fig = px.pie(values=priority_data.values, names=priority_data.index, 
                                title="Debt by Priority")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Debt by lender
                lender_data = debts_df.groupby('lender_name')['current_balance'].sum()
                if not lender_data.empty:
                    fig = px.bar(x=lender_data.index, y=lender_data.values, 
                                title="Debt by Lender")
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("###  Add New Debt")
        
        with st.form("add_debt_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                debt_name = st.text_input("Debt Name*", placeholder="e.g., Car Loan, Credit Card")
                lender_name = st.text_input("Lender Name*", placeholder="e.g., HDFC Bank, Friend")
                original_amount = st.number_input("Original Amount (₹)*", min_value=0.0, step=100.0)
                current_balance = st.number_input("Current Balance (₹)*", min_value=0.0, step=100.0)
                interest_rate = st.number_input("Interest Rate (%)*", min_value=0.0, max_value=100.0, step=0.1)
            
            with col2:
                interest_type = st.selectbox("Interest Type*", ["Simple", "Compound"])
                payment_frequency = st.selectbox("Payment Frequency*", ["Monthly", "Weekly", "Daily"])
                start_date = st.date_input("Start Date*")
                due_date = st.date_input("Due Date (Optional)")
                minimum_payment = st.number_input("Minimum Payment (₹)", min_value=0.0, step=100.0)
                debt_priority = st.selectbox("Priority*", ["High", "Medium", "Low"])
            
            notes = st.text_area("Notes (Optional)", placeholder="Additional notes about this debt...")
            
            submitted = st.form_submit_button("Add Debt")
            
            if submitted:
                if debt_name and lender_name and original_amount > 0 and current_balance > 0:
                    if add_debt(user_id, debt_name, lender_name, original_amount, current_balance,
                               interest_rate, interest_type, payment_frequency, start_date, due_date,
                               minimum_payment, debt_priority, notes):
                        st.success(" Debt added successfully!")
                        st.rerun()
                    else:
                        st.error(" Failed to add debt. Please try again.")
                else:
                    st.error(" Please fill in all required fields.")
    
    with tab3:
        st.markdown("###  Make Debt Payment")
        
        if debts_df.empty:
            st.info("No active debts to make payments on.")
        else:
            # Get debt options for payment
            debt_options = debts_df[['debt_id', 'debt_name', 'lender_name', 'current_balance']].copy()
            debt_options['display'] = debt_options.apply(lambda x: f"{x['debt_name']} - {x['lender_name']} (₹{x['current_balance']:,.0f})", axis=1)
            
            with st.form("make_payment_form"):
                selected_debt = st.selectbox("Select Debt*", options=debt_options['display'].tolist())
                payment_amount = st.number_input("Payment Amount (₹)*", min_value=0.0, step=100.0)
                payment_date = st.date_input("Payment Date*", value=datetime.now().date())
                payment_type = st.selectbox("Payment Type*", ["Regular", "Extra", "Lump Sum"])
                notes = st.text_area("Payment Notes (Optional)", placeholder="Notes about this payment...")
                
                submitted = st.form_submit_button("Make Payment")
                
                if submitted and payment_amount > 0:
                    # Get debt_id from selection
                    selected_index = debt_options[debt_options['display'] == selected_debt].index[0]
                    debt_id = int(debt_options.loc[selected_index, 'debt_id'])
                    current_balance = float(debt_options.loc[selected_index, 'current_balance'])
                    
                    if payment_amount > current_balance:
                        st.warning(f" Payment amount (₹{payment_amount:,.0f}) exceeds current balance (₹{current_balance:,.0f}). The debt will be fully paid.")
                    
                    if add_debt_payment(user_id, debt_id, payment_amount, payment_date, payment_type, notes):
                        st.success(" Payment recorded successfully!")
                        st.rerun()
                    else:
                        st.error(" Failed to record payment. Please try again.")
                elif submitted:
                    st.error(" Please enter a valid payment amount.")
    
    with tab4:
        st.markdown("###  Optimal Repayment Strategy")
        
        if debts_df.empty:
            st.info("No active debts to create repayment strategy for.")
        else:
            # Calculate strategies
            avalanche_strategy = calculate_optimal_repayment_strategy(user_id)
            snowball_strategy = calculate_debt_snowball_strategy(user_id)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("####  Debt Avalanche Method (Recommended)")
                st.markdown("**Strategy**: Pay off debts with the highest interest rates first.")
                st.markdown("**Benefits**: Minimizes total interest paid over time.")
                
                if avalanche_strategy and avalanche_strategy['highest_interest_debt'] is not None:
                    highest_debt = avalanche_strategy['highest_interest_debt']
                    st.info(f"**Priority 1**: {highest_debt['debt_name']} - {highest_debt['lender_name']}")
                    st.info(f"Interest Rate: {highest_debt['interest_rate']:.1f}%")
                    st.info(f"Current Balance: ₹{highest_debt['current_balance']:,.0f}")
                
                st.markdown("**Recommended Order**:")
                if avalanche_strategy['priority_order']:
                    for i, debt in enumerate(avalanche_strategy['priority_order'][:5], 1):
                        st.markdown(f"{i}. {debt['debt_name']} ({debt['lender_name']}) - {debt['interest_rate']:.1f}%")
                else:
                    st.info("No debts available for strategy calculation.")
            
            with col2:
                st.markdown("####  Debt Snowball Method")
                st.markdown("**Strategy**: Pay off debts with the lowest balances first.")
                st.markdown("**Benefits**: Provides psychological wins and motivation.")
                
                if snowball_strategy and snowball_strategy['lowest_balance_debt'] is not None:
                    lowest_debt = snowball_strategy['lowest_balance_debt']
                    st.info(f"**Priority 1**: {lowest_debt['debt_name']} - {lowest_debt['lender_name']}")
                    st.info(f"Current Balance: ₹{lowest_debt['current_balance']:,.0f}")
                    st.info(f"Interest Rate: {lowest_debt['interest_rate']:.1f}%")
                
                st.markdown("**Recommended Order**:")
                if snowball_strategy['priority_order']:
                    for i, debt in enumerate(snowball_strategy['priority_order'][:5], 1):
                        st.markdown(f"{i}. {debt['debt_name']} ({debt['lender_name']}) - ₹{debt['current_balance']:,.0f}")
                else:
                    st.info("No debts available for strategy calculation.")
            
            # Comparison
            st.markdown("###  Strategy Comparison")
            
            if avalanche_strategy and snowball_strategy and avalanche_strategy['highest_interest_debt'] is not None and snowball_strategy['lowest_balance_debt'] is not None:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Debt", f"₹{avalanche_strategy['total_debt']:,.0f}")
                
                with col2:
                    st.metric("Avalanche Priority", f"{avalanche_strategy['highest_interest_debt']['interest_rate']:.1f}% interest")
                
                with col3:
                    st.metric("Snowball Priority", f"₹{snowball_strategy['lowest_balance_debt']['current_balance']:,.0f} balance")
                
                st.markdown("""
                ** Recommendation**: 
                - Use **Debt Avalanche** if you want to save the most money on interest
                - Use **Debt Snowball** if you need motivation and quick wins
                - Both methods work, but avalanche typically saves more money in the long run
                """) 