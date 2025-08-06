import streamlit as st
import pandas as pd
from database import get_mysql_connection
from mysql.connector import Error
from datetime import datetime
import plotly.express as px

def create_goals_tables():
    """Create goals tracking tables if they don't exist"""
    connection = get_mysql_connection()
    if connection is None:
        return
    
    try:
        cursor = connection.cursor()
        
        # Create Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Goals (
                goal_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                goal_name VARCHAR(255) NOT NULL,
                goal_description TEXT,
                target_amount DECIMAL(15,2) NOT NULL,
                current_amount DECIMAL(15,2) DEFAULT 0.00,
                goal_category ENUM('Emergency Fund', 'Vacation', 'Home', 'Car', 'Education', 'Wedding', 'Business', 'Investment', 'Other') DEFAULT 'Other',
                goal_priority ENUM('High', 'Medium', 'Low') DEFAULT 'Medium',
                target_date DATE,
                start_date DATE DEFAULT (CURDATE()),
                goal_status ENUM('Active', 'Completed', 'Paused', 'Cancelled') DEFAULT 'Active',
                monthly_target DECIMAL(15,2),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        ''')
        
        # Create Goal_Contributions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Goal_Contributions (
                contribution_id INT AUTO_INCREMENT PRIMARY KEY,
                goal_id INT NOT NULL,
                user_id INT NOT NULL,
                contribution_amount DECIMAL(15,2) NOT NULL,
                contribution_date DATE NOT NULL,
                contribution_type ENUM('Manual', 'Automatic', 'Bonus', 'Refund', 'Other') DEFAULT 'Manual',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES Goals(goal_id),
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        ''')
        
        connection.commit()
        cursor.close()
        connection.close()
        
    except Exception as e:
        st.error(f"Error creating goals tables: {e}")

def add_goal(user_id, goal_name, goal_description, target_amount, goal_category, 
             goal_priority, target_date, monthly_target, notes):
    """Add a new financial goal for a user"""
    connection = get_mysql_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Convert data types
        user_id = int(user_id)
        target_amount = float(target_amount)
        monthly_target = float(monthly_target) if monthly_target else None
        
        cursor.execute('''
            INSERT INTO Goals (user_id, goal_name, goal_description, target_amount, 
                              goal_category, goal_priority, target_date, monthly_target, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, goal_name, goal_description, target_amount, goal_category,
              goal_priority, target_date, monthly_target, notes))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        st.error(f"Error adding goal: {e}")
        return False

def get_user_goals(user_id):
    """Get all goals for a user"""
    connection = get_mysql_connection()
    if connection is None:
        return pd.DataFrame()
    
    try:
        query = '''
            SELECT goal_id, goal_name, goal_description, target_amount, current_amount,
                   goal_category, goal_priority, target_date, start_date, goal_status,
                   monthly_target, notes,
                   DATEDIFF(target_date, CURDATE()) as days_remaining,
                   ROUND((current_amount / target_amount) * 100, 2) as progress_percentage,
                   ROUND((target_amount - current_amount), 2) as remaining_amount
            FROM Goals 
            WHERE user_id = %s
            ORDER BY goal_priority DESC, target_date ASC
        '''
        df = pd.read_sql_query(query, connection, params=(user_id,))
        connection.close()
        return df
    except Exception as e:
        st.error(f"Error fetching goals: {e}")
        return pd.DataFrame()

def add_goal_contribution(user_id, goal_id, contribution_amount, contribution_date, 
                         contribution_type, notes):
    """Add a contribution to a goal"""
    connection = get_mysql_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Convert data types
        goal_id = int(goal_id)
        user_id = int(user_id)
        contribution_amount = float(contribution_amount)
        
        # Add contribution record
        cursor.execute('''
            INSERT INTO Goal_Contributions (goal_id, user_id, contribution_amount, 
                                          contribution_date, contribution_type, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (goal_id, user_id, contribution_amount, contribution_date, 
              contribution_type, notes))
        
        # Update goal current amount
        cursor.execute('''
            UPDATE Goals 
            SET current_amount = current_amount + %s
            WHERE goal_id = %s AND user_id = %s
        ''', (contribution_amount, goal_id, user_id))
        
        # Check if goal is completed
        cursor.execute('''
            UPDATE Goals 
            SET goal_status = 'Completed'
            WHERE goal_id = %s AND user_id = %s AND current_amount >= target_amount
        ''', (goal_id, user_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        st.error(f"Error adding goal contribution: {e}")
        return False

def get_goal_contributions(user_id, goal_id=None):
    """Get goal contributions for a user"""
    connection = get_mysql_connection()
    if connection is None:
        return pd.DataFrame()
    
    try:
        if goal_id:
            query = '''
                SELECT gc.contribution_id, gc.contribution_amount, gc.contribution_date,
                       gc.contribution_type, gc.notes, g.goal_name
                FROM Goal_Contributions gc
                JOIN Goals g ON gc.goal_id = g.goal_id
                WHERE gc.user_id = %s AND gc.goal_id = %s
                ORDER BY gc.contribution_date DESC
            '''
            df = pd.read_sql_query(query, connection, params=(user_id, goal_id))
        else:
            query = '''
                SELECT gc.contribution_id, gc.contribution_amount, gc.contribution_date,
                       gc.contribution_type, gc.notes, g.goal_name
                FROM Goal_Contributions gc
                JOIN Goals g ON gc.goal_id = g.goal_id
                WHERE gc.user_id = %s
                ORDER BY gc.contribution_date DESC
            '''
            df = pd.read_sql_query(query, connection, params=(user_id,))
        
        connection.close()
        return df
    except Exception as e:
        st.error(f"Error fetching goal contributions: {e}")
        return pd.DataFrame()

def calculate_goal_insights(user_id):
    """Calculate insights about user's goals"""
    goals_df = get_user_goals(user_id)
    if goals_df.empty:
        return None
    
    # Calculate insights
    total_goals = len(goals_df)
    active_goals = len(goals_df[goals_df['goal_status'] == 'Active'])
    completed_goals = len(goals_df[goals_df['goal_status'] == 'Completed'])
    
    total_target = goals_df['target_amount'].sum()
    total_current = goals_df['current_amount'].sum()
    total_progress = (total_current / total_target * 100) if total_target > 0 else 0
    
    # Average progress
    avg_progress = goals_df['progress_percentage'].mean()
    
    # Goals by category
    category_distribution = goals_df.groupby('goal_category')['target_amount'].sum()
    
    # Goals by priority
    priority_distribution = goals_df.groupby('goal_priority')['target_amount'].sum()
    
    # Upcoming deadlines (within 30 days)
    upcoming_deadlines = goals_df[
        (goals_df['days_remaining'] >= 0) & 
        (goals_df['days_remaining'] <= 30) & 
        (goals_df['goal_status'] == 'Active')
    ]
    
    insights = {
        'total_goals': total_goals,
        'active_goals': active_goals,
        'completed_goals': completed_goals,
        'total_target': total_target,
        'total_current': total_current,
        'total_progress': total_progress,
        'avg_progress': avg_progress,
        'category_distribution': category_distribution,
        'priority_distribution': priority_distribution,
        'upcoming_deadlines': upcoming_deadlines
    }
    
    return insights

def goals_management_page():
    """Display the goals management interface"""
    st.markdown('<h1 class="main-header">🎯 Financial Goals Manager</h1>', unsafe_allow_html=True)
    
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
        if st.button("📊 Advanced Analytics"):
            st.session_state.current_page = "analytics"
            st.rerun()
    with col6:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.rerun()
    
    # Check if user is authenticated
    if not st.session_state.get('authenticated', False):
        st.error("Please login first to access the goals manager.")
        return
    
    user_id = st.session_state.get('user_id')
    user_name = st.session_state.get('user_name')
    
    if not user_id:
        st.error("User ID not found. Please login again.")
        return
    
    # Create goals tables if they don't exist
    create_goals_tables()
    
    # Get user goals and insights
    goals_df = get_user_goals(user_id)
    insights = calculate_goal_insights(user_id)
    
    # Tabs for different goal management features
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Goals Overview", "➕ Add Goal", "💰 Add Contribution", "📈 Progress Tracking"])
    
    with tab1:
        st.markdown("### 📊 Your Financial Goals Overview")
        
        if goals_df.empty:
            st.info("🎯 You haven't set any financial goals yet. Start by adding your first goal!")
            st.markdown("""
            **💡 Why set financial goals?**
            - 🎯 Stay focused on what matters most
            - 📈 Track your progress over time
            - 💰 Build wealth systematically
            - 🏆 Celebrate achievements
            - 📊 Make informed financial decisions
            """)
        else:
            # Goals summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎯 Total Goals", insights['total_goals'])
            with col2:
                st.metric("📈 Active Goals", insights['active_goals'])
            with col3:
                st.metric("✅ Completed Goals", insights['completed_goals'])
            with col4:
                st.metric("📊 Overall Progress", f"{insights['total_progress']:.1f}%")
            
            # Progress overview
            col1, col2 = st.columns(2)
            with col1:
                st.metric("💰 Total Target", f"₹{insights['total_target']:,.0f}")
            with col2:
                st.metric("💵 Total Saved", f"₹{insights['total_current']:,.0f}")
            
            # Display goals with progress bars
            st.markdown("### 🎯 Your Goals")
            
            for _, goal in goals_df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{goal['goal_name']}**")
                        st.markdown(f"*{goal['goal_description']}*")
                        st.markdown(f"Category: {goal['goal_category']} | Priority: {goal['goal_priority']}")
                        
                        # Progress bar
                        progress = goal['progress_percentage'] / 100
                        st.progress(progress)
                        st.markdown(f"₹{goal['current_amount']:,.0f} / ₹{goal['target_amount']:,.0f} ({goal['progress_percentage']:.1f}%)")
                    
                    with col2:
                        if goal['goal_status'] == 'Active':
                            st.success("🟢 Active")
                        elif goal['goal_status'] == 'Completed':
                            st.success("✅ Completed")
                        elif goal['goal_status'] == 'Paused':
                            st.warning("⏸️ Paused")
                        else:
                            st.error("❌ Cancelled")
                    
                    with col3:
                        if goal['days_remaining'] > 0:
                            st.info(f"📅 {goal['days_remaining']} days left")
                        elif goal['days_remaining'] < 0:
                            st.error(f"⚠️ {abs(goal['days_remaining'])} days overdue")
                        else:
                            st.warning("📅 Due today")
                    
                    with col4:
                        if goal['goal_status'] == 'Active':
                            if st.button("💰 Add", key=f"add_cont_{goal['goal_id']}"):
                                st.session_state.selected_goal = goal['goal_id']
                                st.session_state.current_tab = "tab3"
                                st.rerun()
                
                st.markdown("---")
            
            # Goals charts
            if not goals_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Goals by category
                    category_data = goals_df.groupby('goal_category')['target_amount'].sum()
                    if not category_data.empty:
                        fig = px.pie(values=category_data.values, names=category_data.index, 
                                    title="Goals by Category")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Goals by priority
                    priority_data = goals_df.groupby('goal_priority')['target_amount'].sum()
                    if not priority_data.empty:
                        fig = px.bar(x=priority_data.index, y=priority_data.values, 
                                    title="Goals by Priority")
                        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### ➕ Add New Financial Goal")
        
        with st.form("add_goal_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                goal_name = st.text_input("Goal Name*", placeholder="e.g., Emergency Fund, Vacation to Europe")
                goal_description = st.text_area("Goal Description*", placeholder="Describe your goal in detail...")
                target_amount = st.number_input("Target Amount (₹)*", min_value=100.0, step=1000.0)
                goal_category = st.selectbox("Goal Category*", [
                    "Emergency Fund", "Vacation", "Home", "Car", "Education", 
                    "Wedding", "Business", "Investment", "Other"
                ])
            
            with col2:
                goal_priority = st.selectbox("Priority*", ["High", "Medium", "Low"])
                target_date = st.date_input("Target Date (Optional)")
                monthly_target = st.number_input("Monthly Target (₹)", min_value=0.0, step=100.0, help="How much you plan to save monthly")
                notes = st.text_area("Additional Notes (Optional)", placeholder="Any additional notes...")
            
            submitted = st.form_submit_button("Create Goal")
            
            if submitted:
                if goal_name and goal_description and target_amount > 0:
                    if add_goal(user_id, goal_name, goal_description, target_amount, goal_category,
                               goal_priority, target_date, monthly_target, notes):
                        st.success("✅ Goal created successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Failed to create goal. Please try again.")
                else:
                    st.error("❌ Please fill in all required fields.")
        
        # Goal templates
        st.markdown("### 💡 Popular Goal Templates")
        
        templates = [
            {
                "name": "Emergency Fund",
                "description": "Save 6 months of living expenses for unexpected situations",
                "category": "Emergency Fund",
                "priority": "High"
            },
            {
                "name": "Vacation Fund",
                "description": "Save for your dream vacation or travel experiences",
                "category": "Vacation",
                "priority": "Medium"
            },
            {
                "name": "Home Down Payment",
                "description": "Save for a down payment on your dream home",
                "category": "Home",
                "priority": "High"
            },
            {
                "name": "Car Purchase",
                "description": "Save to buy a car without taking a loan",
                "category": "Car",
                "priority": "Medium"
            }
        ]
        
        cols = st.columns(2)
        for i, template in enumerate(templates):
            with cols[i % 2]:
                with st.expander(f"📋 {template['name']}"):
                    st.markdown(f"**Description**: {template['description']}")
                    st.markdown(f"**Category**: {template['category']}")
                    st.markdown(f"**Priority**: {template['priority']}")
                    
                    if st.button(f"Use Template", key=f"template_{i}"):
                        st.session_state.template = template
                        st.rerun()
    
    with tab3:
        st.markdown("### 💰 Add Contribution to Goal")
        
        if goals_df.empty:
            st.info("No goals available. Create a goal first to add contributions.")
        else:
            # Get active goals for contribution
            active_goals = goals_df[goals_df['goal_status'] == 'Active']
            
            if active_goals.empty:
                st.info("No active goals to contribute to. Complete your existing goals or create new ones.")
            else:
                # Check if a goal was selected from overview
                selected_goal_id = st.session_state.get('selected_goal')
                
                with st.form("add_contribution_form"):
                    # Goal selection
                    if selected_goal_id:
                        selected_goal = active_goals[active_goals['goal_id'] == selected_goal_id]
                        if not selected_goal.empty:
                            goal_display = f"{selected_goal.iloc[0]['goal_name']} - ₹{selected_goal.iloc[0]['current_amount']:,.0f} / ₹{selected_goal.iloc[0]['target_amount']:,.0f}"
                            st.info(f"Selected Goal: {goal_display}")
                            goal_options = active_goals[active_goals['goal_id'] == selected_goal_id]
                        else:
                            goal_options = active_goals
                    else:
                        goal_options = active_goals
                    
                    # Create goal options for dropdown
                    goal_choices = goal_options[['goal_id', 'goal_name', 'current_amount', 'target_amount']].copy()
                    goal_choices['display'] = goal_choices.apply(
                        lambda x: f"{x['goal_name']} (₹{x['current_amount']:,.0f} / ₹{x['target_amount']:,.0f})", 
                        axis=1
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        selected_goal_display = st.selectbox(
                            "Select Goal*", 
                            options=goal_choices['display'].tolist(),
                            index=0 if not selected_goal_id else 0
                        )
                        contribution_amount = st.number_input(
                            "Contribution Amount (₹)*", 
                            min_value=1.0, 
                            step=100.0
                        )
                        contribution_date = st.date_input(
                            "Contribution Date*", 
                            value=datetime.now().date()
                        )
                    
                    with col2:
                        contribution_type = st.selectbox(
                            "Contribution Type*", 
                            ["Manual", "Automatic", "Bonus", "Refund", "Other"]
                        )
                        notes = st.text_area(
                            "Notes (Optional)", 
                            placeholder="Notes about this contribution..."
                        )
                    
                    submitted = st.form_submit_button("Add Contribution")
                    
                    if submitted and contribution_amount > 0:
                        # Get goal_id from selection
                        selected_index = goal_choices[goal_choices['display'] == selected_goal_display].index[0]
                        goal_id = int(goal_choices.loc[selected_index, 'goal_id'])
                        
                        if add_goal_contribution(user_id, goal_id, contribution_amount, 
                                               contribution_date, contribution_type, notes):
                            st.success("✅ Contribution added successfully!")
                            st.balloons()
                            
                            # Clear selected goal from session state
                            if 'selected_goal' in st.session_state:
                                del st.session_state.selected_goal
                            
                            st.rerun()
                        else:
                            st.error("❌ Failed to add contribution. Please try again.")
                    elif submitted:
                        st.error("❌ Please enter a valid contribution amount.")
    
    with tab4:
        st.markdown("### 📈 Progress Tracking & Insights")
        
        if goals_df.empty:
            st.info("No goals to track. Create some goals to see your progress insights.")
        else:
            # Progress insights
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Overall Progress")
                st.metric("Average Progress", f"{insights['avg_progress']:.1f}%")
                st.metric("Total Saved", f"₹{insights['total_current']:,.0f}")
                st.metric("Remaining to Save", f"₹{insights['total_target'] - insights['total_current']:,.0f}")
            
            with col2:
                st.markdown("#### 🎯 Goal Status")
                st.metric("Active Goals", insights['active_goals'])
                st.metric("Completed Goals", insights['completed_goals'])
                st.metric("Completion Rate", f"{(insights['completed_goals'] / insights['total_goals'] * 100):.1f}%")
            
            # Upcoming deadlines
            if not insights['upcoming_deadlines'].empty:
                st.markdown("#### ⚠️ Upcoming Deadlines (Next 30 Days)")
                for _, goal in insights['upcoming_deadlines'].iterrows():
                    st.warning(f"**{goal['goal_name']}** - Due in {goal['days_remaining']} days. Progress: {goal['progress_percentage']:.1f}%")
            
            # Progress trends
            st.markdown("#### 📈 Progress Trends")
            
            # Get contributions over time
            contributions_df = get_goal_contributions(user_id)
            if not contributions_df.empty:
                contributions_df['contribution_date'] = pd.to_datetime(contributions_df['contribution_date'])
                monthly_contributions = contributions_df.groupby(
                    contributions_df['contribution_date'].dt.to_period('M')
                )['contribution_amount'].sum().reset_index()
                monthly_contributions['contribution_date'] = monthly_contributions['contribution_date'].astype(str)
                
                fig = px.line(
                    monthly_contributions,
                    x='contribution_date',
                    y='contribution_amount',
                    title="Monthly Contributions to Goals"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Goal recommendations
            st.markdown("#### 💡 Smart Recommendations")
            
            if insights['avg_progress'] < 50:
                st.info("🎯 **Focus on High-Priority Goals**: Your average progress is below 50%. Consider focusing on high-priority goals first.")
            
            if insights['active_goals'] > 5:
                st.warning("📊 **Too Many Active Goals**: You have many active goals. Consider pausing some to focus on the most important ones.")
            
            if insights['total_progress'] > 80:
                st.success("🏆 **Great Progress**: You're making excellent progress! Keep up the momentum.")
            
            # Contribution history
            st.markdown("#### 📋 Recent Contributions")
            recent_contributions = get_goal_contributions(user_id)
            if not recent_contributions.empty:
                st.dataframe(
                    recent_contributions.head(10),
                    use_container_width=True,
                    column_config={
                        "contribution_amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
                        "contribution_date": st.column_config.DateColumn("Date")
                    }
                )
            else:
                st.info("No contributions recorded yet. Start contributing to your goals!") 