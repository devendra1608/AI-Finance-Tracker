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
from loan_comparison import loan_comparison_page
from investments import investments_page

# Page configuration
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling


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
        if st.session_state.authenticated:
            st.session_state.current_page = "dashboard"
            st.rerun()

    else:
        # 🟩 NAVBAR CSS only after login
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 4rem !important;
                }    
                .stAppToolbar {
                    height: 80px !important;
                    background-color: #363636;
                    padding: 0rem 2rem !important;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                    align-items: center;
                }
                .rc-overflow {
                    display: flex;
                    gap: 1rem;
                    height: 100%;
                }
                .rc-overflow-item {
                    font-size: 100px;
                    width: 9rem;
                    margin-right: 10px;
                    transition: all 0.3s ease;
                }
                .rc-overflow-item {
                    margin-top: 1rem;
                    font-size: 30px;
                    border-radius: 8px;
                    cursor: pointer;
                }
                .rc-overflow-item > div:hover {
                    color: #007bff;
                }
                .rc-overflow-item[aria-current="page"] > div {
                    background-color: #007bff;
                    color: white;
                    border: none;
                }
            </style>
        """, unsafe_allow_html=True)

        # 🟩 Navigation pages
        pages = [
            st.Page(dashboard, title="Dashboard", icon="📊"),
            st.Page(transaction_page, title="Transactions", icon="💳"),
            st.Page(advanced_analytics_page, title="Analytics", icon="📈"),
            st.Page(goals_management_page, title="Goals", icon="🎯"),
            st.Page(chatbot_page, title="AI Assistant", icon="🤖"),
            st.Page(debt_tracker_page, title="Debt Tracker", icon="📋"),
            st.Page(loan_comparison_page, title="Loan Comparison", icon="🏦"),
            st.Page(investments_page, title="Investments", icon="💹"),  
        ]

        pg = st.navigation(pages, position="top", expanded=True)

        # 🟩 Logout Button
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
