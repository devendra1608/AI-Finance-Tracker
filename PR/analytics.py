import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_mysql_connection
from mysql.connector import Error

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
        
        # 5. Income vs Expense ratio by month
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
        
        if not monthly_ratio.empty:
            monthly_ratio['TotalIncome'] = pd.to_numeric(monthly_ratio['TotalIncome'], errors='coerce')
            monthly_ratio['TotalExpense'] = pd.to_numeric(monthly_ratio['TotalExpense'], errors='coerce')
            monthly_ratio['NetAmount'] = pd.to_numeric(monthly_ratio['NetAmount'], errors='coerce')
        
        return {
            'daily_data': daily_data,
            'category_trends': category_trends,
            'payment_analysis': payment_analysis,
            'weekly_patterns': weekly_patterns,
            'monthly_ratio': monthly_ratio
        }
    except Error as e:
        st.error(f"Error fetching advanced analytics: {e}")
        return {}

def advanced_analytics_page():
    """Display advanced analytics page with comprehensive spending trends"""
    st.markdown(f'<h1 class="main-header">📊 Advanced Analytics - {st.session_state.user_name}</h1>', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()
    with col2:
        if st.button("💰 Add Transaction"):
            st.session_state.current_page = "transaction"
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
        
        # Top categories line chart
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