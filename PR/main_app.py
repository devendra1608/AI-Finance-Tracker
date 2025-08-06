import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import all modules
from database import get_mysql_connection
from auth import login_page
from dashboard import dashboard
from transactions import transaction_page
from chatbot import chatbot_page
from debt_tracker import debt_tracker_page
from goals_manager import goals_management_page
from analytics import advanced_analytics_page

# Page configuration
st.set_page_config(
    page_title="Dabba - Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Hide the default navigation if needed */
    .stSidebar {
        display: none;
    }
    
    /* Custom styling for the app */
    .main-header {
        padding: 1rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

def main():
    """Main application function"""
    # Show login/signup page first
    if not st.session_state.authenticated:
        login_page()
        # If login is successful, rerun to load dashboard and navigation
        if st.session_state.authenticated:
            st.session_state.current_page = "dashboard"
            st.rerun()
    else:
        # Navigation bar and pages only after authentication
        pages = [
            st.Page(dashboard, title="Dashboard", icon="📊"),
            st.Page(transaction_page, title="Transactions", icon="💳"),
            st.Page(advanced_analytics_page, title="Analytics", icon="📈"),
            st.Page(chatbot_page, title="AI Assistant", icon="🤖"),
            st.Page(debt_tracker_page, title="Debt Tracker", icon="📋"),
            st.Page(goals_management_page, title="Goals", icon="🎯"),
        ]
        pg = st.navigation(pages, position="top", expanded=True)
        # Add logout functionality
        col1, col2, col3 = st.columns([6, 1, 0.6])
        with col3:
            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_id = None
                st.session_state.user_name = None
                st.rerun()
        pg.run()

if __name__ == "__main__":
    main()
