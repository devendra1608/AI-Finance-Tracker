import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database import get_user_data, get_user_summary, get_category_data, get_monthly_trends

def dashboard():
    """Display main dashboard after login"""
    st.markdown(f'<h1 class="main-header">💰 Welcome, {st.session_state.user_name}! 👋</h1>', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        if st.button("📊 Advanced Analytics"):
            st.session_state.current_page = "analytics"
            st.rerun()
    with col2:
        if st.button("🤖 AI Chatbot"):
            st.session_state.current_page = "chatbot"
            st.rerun()
    with col3:
        if st.button("💰 Add Transaction"):
            st.session_state.current_page = "transaction"
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