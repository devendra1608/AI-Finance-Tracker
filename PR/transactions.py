import streamlit as st
from datetime import datetime
from database import insert_transaction, get_user_data, get_user_summary, get_available_categories, get_available_modes

def transaction_page():
    """Display the transaction insertion page"""
    st.markdown(f'<h1 class="main-header">💰 Add New Transaction - {st.session_state.user_name}</h1>', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()
    with col2:
        if st.button("📊 Advanced Analytics"):
            st.session_state.current_page = "analytics"
            st.rerun()
    with col3:
        if st.button("🤖 AI Chatbot"):
            st.session_state.current_page = "chatbot"
            st.rerun()
    with col4:
        if st.button("💳 Debt Tracker"):
            st.session_state.current_page = "debt"
            st.rerun()
    with col5:
        if st.button("🎯 Goals Manager"):
            st.session_state.current_page = "goals"
            st.rerun()
    with col6:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.rerun()
    
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
    
    st.markdown("### 📝 Add New Transaction")
    
    # Transaction form
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Date picker
            transaction_date = st.date_input(
                "📅 Transaction Date",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
            
            # Amount input
            amount = st.number_input(
                "💰 Amount (₹)",
                min_value=0.01,
                max_value=1000000.00,
                value=100.00,
                step=0.01,
                format="%.2f"
            )
            
            # Transaction type
            transaction_type = st.selectbox(
                "📊 Transaction Type",
                options=["Expense", "Income"],
                index=0
            )
        
        with col2:
            # Payment mode
            payment_mode = st.selectbox(
                "💳 Payment Mode",
                options=all_modes,
                index=0
            )
            
            # Category
            category = st.selectbox(
                "🏷️ Category",
                options=all_categories,
                index=0
            )
            
            # Currency (default to INR)
            currency = st.selectbox(
                "💱 Currency",
                options=["INR", "USD", "EUR", "GBP"],
                index=0
            )
        
        # Custom category input
        st.markdown("**Or enter a custom category:**")
        custom_category = st.text_input(
            "🏷️ Custom Category (optional)",
            placeholder="Enter custom category if not in the list above"
        )
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button("💾 Save Transaction", use_container_width=True)
        
        if submit_button:
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
                    st.balloons()
                    
                    # Show transaction summary
                    st.markdown("### 📋 Transaction Summary")
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
                    st.markdown("### 📊 Updated Financial Summary")
                    updated_summary = get_user_summary(st.session_state.user_id)
                    if updated_summary:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("💰 Total Income", f"₹{updated_summary['total_income']:,.0f}")
                        with col2:
                            st.metric("💸 Total Expenses", f"₹{updated_summary['total_expenses']:,.0f}")
                        with col3:
                            st.metric("📊 Net Balance", f"₹{updated_summary['net_balance']:,.0f}")
                        with col4:
                            st.metric("📅 Total Transactions", updated_summary['transaction_count'])
                else:
                    st.error("❌ Failed to add transaction. Please try again.")
    
    # Recent transactions for reference
    st.markdown("### 📋 Your Recent Transactions")
    recent_data = get_user_data(st.session_state.user_id)
    if not recent_data.empty:
        st.dataframe(
            recent_data.head(10), 
            use_container_width=True,
            column_config={
                "Date": st.column_config.DateColumn("Date"),
                "Amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
                "income_expense": st.column_config.SelectboxColumn("Type", options=["Income", "Expense"])
            }
        )
    else:
        st.info("💡 No transactions found. Add your first transaction above!")
    
    # Popular categories and payment modes
    st.markdown("### 📈 Your Most Used Categories & Payment Modes")
    
    # Get user's most used categories and payment modes
    user_data = get_user_data(st.session_state.user_id)
    if not user_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🏷️ Your Top Categories**")
            category_counts = user_data['Category'].value_counts().head(5)
            if not category_counts.empty:
                for category, count in category_counts.items():
                    st.markdown(f"• **{category}**: {count} transactions")
            else:
                st.info("No category data available yet.")
        
        with col2:
            st.markdown("**💳 Your Payment Methods**")
            mode_counts = user_data['Mode'].value_counts().head(5)
            if not mode_counts.empty:
                for mode, count in mode_counts.items():
                    st.markdown(f"• **{mode}**: {count} transactions")
            else:
                st.info("No payment method data available yet.")
    
    # Quick tips
    st.markdown("### 💡 Quick Tips")
    tips = [
        "💡 Use specific categories to better track your spending patterns",
        "💡 Regular transactions help build better financial insights",
        "💡 You can add custom categories for unique expenses",
        "💡 All transactions are automatically linked to your account",
        "💡 Check the dashboard to see your updated financial summary"
    ]
    
    for tip in tips:
        st.markdown(tip) 