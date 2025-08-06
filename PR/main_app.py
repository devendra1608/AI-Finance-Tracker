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
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
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
    # Initialize current page in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    if not st.session_state.authenticated:
        login_page()
    else:
        if st.session_state.current_page == "analytics":
            # Import analytics module dynamically to avoid circular imports
            try:
                from analytics import advanced_analytics_page
                advanced_analytics_page()
            except ImportError:
                st.error("Analytics module not available. Please check the analytics.py file.")
        elif st.session_state.current_page == "chatbot":
            chatbot_page()
        elif st.session_state.current_page == "transaction":
            transaction_page()
        elif st.session_state.current_page == "debt":
            debt_tracker_page()
        elif st.session_state.current_page == "goals":
            goals_management_page()
        else:
            dashboard()

if __name__ == "__main__":
    main() 