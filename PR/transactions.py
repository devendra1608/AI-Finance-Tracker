import streamlit as st
from datetime import datetime
from database import insert_transaction, get_user_data, get_user_summary, get_available_categories, get_available_modes, get_mysql_connection
import pandas as pd 
def transaction_page():
    """Display the transaction insertion page"""
    st.markdown(f'<h1 class="main-header"> Transactions </h1>', unsafe_allow_html=True)
    
    
    # Get available categories and modes
    available_categories = get_available_categories()
    available_modes = get_available_modes()
    
    # Default options
    default_categories = [
        "Food", "Travel", "Shopping", "College", "Transfer", "Entertainment", 
        "Stationery", "Electronics", "Product", "Grocery", "Clothes", "Other",
        "Laundry", "Delivery", "Cricket", "Rapido", "Bus", "Metro", "Highway",
        "Salon", "Railways", "Recharge", "Medicine", "Sports", "Amazon",
        "IRCTC", "Neelkanta", "Boutique", "General store", "Hospital",
        "Vegetables", "Kirana", "Swayam", "Salary", "Freelance", "Investment",
        "Gifts", "Health", "Utilities"
    ]
    
    default_modes = [
        "UPI", "Cash", "Debit Card", "Credit Card", "Bank Transfer"
    ]
    
    # Combine existing and default options
    all_categories = list(set(available_categories + default_categories))
    all_modes = list(set(available_modes + default_modes))
    
    # Sort for better UX
    all_categories.sort()
    all_modes.sort()
    
        
    # Recent transactions for reference
    conn = get_mysql_connection()
    cursor = conn.cursor()

    user_id = st.session_state.user_id

    # Fetch transactions
    cursor.execute("SELECT  Date, Mode, Category, Amount, income_expense, Currency FROM data WHERE id = %s ORDER BY Date DESC", (user_id,))
    results = cursor.fetchall()
    conn.close()

    if not results:
        st.info("No transactions found.")
        return

    # Prepare DataFrame
    user_data = pd.DataFrame(results, columns=[ "Date", "Mode", "Category", "Amount", "Income_Expense", "Currency"])
    
    # Convert Date column to datetime
    user_data['Date'] = pd.to_datetime(user_data['Date'], errors='coerce')

    # --- FILTERS ---
    st.markdown("### Filters", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])

    with col1:
        filter_month = st.selectbox("Month", ["All"] + sorted(user_data['Date'].dt.strftime('%B').unique().tolist()))
    with col2:
        filter_year = st.selectbox("Year", ["All"] + sorted(user_data['Date'].dt.year.dropna().unique().astype(str).tolist()))
    with col3:
        filter_category = st.selectbox("Category", ["All"] + sorted(user_data['Category'].dropna().unique().tolist()))
    with col4:
        add_clicked = st.button("➕ Add Transaction", use_container_width=True)

    # --- MODAL FORM ---
    if add_clicked:
        st.markdown(
            """
            <style>
            .modal-container {
                position: fixed;
                top: 0; left: 0;
                width: 100vw; height: 100vh;
                background: rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(5px);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            }
            .modal-form {
                background-color: #222;
                padding: 20px;
                border-radius: 12px;
                width: 350px;
            }
            .close-button {
                float: right;
                font-size: 18px;
                color: #999;
                cursor: pointer;
            }
            </style>
            <div class='modal-container'>
                <div class='modal-form'>
                    <span class='close-button' onclick='window.location.reload()'>✕</span>
            """,
            unsafe_allow_html=True
        )
        with st.form("transaction_form"):
            col1, col2 = st.columns(2)
            with col1:
                transaction_date = st.date_input("Transaction Date", value=datetime.now().date())
                amount = st.number_input("Amount (₹)", min_value=0.01, value=100.0, step=0.01, format="%.2f")
                transaction_type = st.selectbox("Transaction Type", ["Expense", "Income"])
            with col2:
                payment_mode = st.selectbox("Payment Mode", all_modes)
                category = st.selectbox("Category", all_categories)
                currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"], index=0)

            custom_category = st.text_input("Custom Category (optional)", placeholder="Enter custom category")

            submit = st.form_submit_button("💾 Save Transaction")
            if submit:
                # Validate inputs
                if not transaction_date:
                    st.error("❌ Please select a transaction date.")
                elif amount <= 0:
                    st.error("❌ Amount must be greater than 0.")
                elif not payment_mode:
                    st.error("❌ Please select a payment mode.")
                elif not category and not custom_category:
                    st.error("❌ Please select a category or enter a custom one.")
                else:
                    # Use custom category if provided, otherwise use selected category
                    final_category = custom_category if custom_category else category
                    
                    # Insert transaction
                    success = insert_transaction(
                        st.session_state.user_id,
                        transaction_date,
                        payment_mode,
                        final_category,
                        amount,
                        transaction_type,
                        currency
                    )
                    
                if success:
                    st.success(f"✅ Transaction added successfully!")
                        
                        # Show transaction summary
                    st.markdown("###  Transaction Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Date", transaction_date.strftime("%Y-%m-%d"))
                        st.metric("Amount", f"₹{amount:,.2f}")
                        st.metric("Type", transaction_type)
                    with col2:
                        st.metric("Payment Mode", payment_mode)
                        st.metric("Category", final_category)
                        st.metric("Currency", currency)
                        
                        # Show updated financial summary
                        st.markdown("###  Updated Financial Summary")
                        updated_summary = get_user_summary(st.session_state.user_id)
                        if updated_summary:
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(" Total Income", f"₹{updated_summary['total_income']:,.0f}")
                            with col2:
                                st.metric("💸 Total Expenses", f"₹{updated_summary['total_expenses']:,.0f}")
                            with col3:
                                st.metric(" Net Balance", f"₹{updated_summary['net_balance']:,.0f}")
                            with col4:
                                st.metric(" Total Transactions", updated_summary['transaction_count'])
                        else:
                            st.error("❌ Failed to add transaction. Please try again.")
    

    filtered_data = user_data.copy()
    if filter_month != "All":
        filtered_data = filtered_data[filtered_data['Date'].dt.strftime('%B') == filter_month]
    if filter_year != "All":
        filtered_data = filtered_data[filtered_data['Date'].dt.year.astype(str) == filter_year]
    if filter_category != "All":
        filtered_data = filtered_data[filtered_data['Category'] == filter_category]

    # --- SHOW TRANSACTIONS ---
    st.markdown("### Recent Transactions", unsafe_allow_html=True)
    
    if filtered_data.empty:
        st.warning("No transactions found.")
    else:
        filtered_data = filtered_data.sort_values(by="Date", ascending=False)

        # Show only top 15
        st.dataframe(
            filtered_data,
            use_container_width=True,
            height=600
        )

    cursor.close()
    conn.close()
    # Get user's most used categories and payment modes
    user_data = get_user_data(st.session_state.user_id)
    if not user_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("** Your Top Categories**")
            category_counts = user_data['Category'].value_counts().head(5)
            if not category_counts.empty:
                for category, count in category_counts.items():
                    st.markdown(f"• **{category}**: {count} transactions")
            else:
                st.info("No category data available yet.")
        
        with col2:
            st.markdown("** Your Payment Methods**")
            mode_counts = user_data['Mode'].value_counts().head(5)
            if not mode_counts.empty:
                for mode, count in mode_counts.items():
                    st.markdown(f"• **{mode}**: {count} transactions")
            else:
                st.info("No payment method data available yet.")
    
    