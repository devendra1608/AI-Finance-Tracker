import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

INVESTMENT_OPTIONS = {
    "fixed_deposit": "Fixed Deposit",
    "recurring_deposit": "Recurring Deposit",
    "savings_account": "Savings Account"
}

FD_URL = "https://www.bankbazaar.com/fixed-deposit-rate.html"
RD_URL = "https://www.bankbazaar.com/recurring-deposit-rates.html"
SA_URL = "https://www.bankbazaar.com/savings-account.html"

def fetch_fd_tables():
    response = requests.get(FD_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table")
    fd_tables = {}
    # Identify tables by their headings
    headings = [h.get_text(strip=True) for h in soup.find_all(["h2", "h3"])]
    for idx, table in enumerate(tables):
        if idx < len(headings):
            title = headings[idx]
        else:
            title = f"Table {idx+1}"
        df = pd.read_html(str(table))[0]
        fd_tables[title] = df
    return fd_tables

def fetch_rd_tables():
    response = requests.get(RD_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table")
    rd_tables = {}
    headings = [h.get_text(strip=True) for h in soup.find_all(["h2", "h3"])]
    for idx, table in enumerate(tables):
        if idx < len(headings):
            title = headings[idx]
        else:
            title = f"Table {idx+1}"
        df = pd.read_html(str(table))[0]
        rd_tables[title] = df
    return rd_tables

def fetch_sa_tables():
    response = requests.get(SA_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table")
    sa_tables = {}
    headings = [h.get_text(strip=True) for h in soup.find_all(["h2", "h3"])]
    for idx, table in enumerate(tables):
        if idx < len(headings):
            title = headings[idx]
        else:
            title = f"Table {idx+1}"
        df = pd.read_html(str(table))[0]
        sa_tables[title] = df
    return sa_tables

def investments_page():
    st.markdown("<h1> Investments</h1>", unsafe_allow_html=True)
    option = st.selectbox(
        "Choose Investment Type:",
        options=list(INVESTMENT_OPTIONS.keys()),
        format_func=lambda x: INVESTMENT_OPTIONS[x]
    )
    st.markdown(f"### {INVESTMENT_OPTIONS[option]}")
    if option == "fixed_deposit":
        # st.info("Showing Fixed Deposit Interest Rates (Live from BankBazaar)")
        fd_tables = fetch_fd_tables()
        for title, df in fd_tables.items():
            st.markdown(f"#### {title}")
            st.dataframe(df, use_container_width=True)
    elif option == "recurring_deposit":
        # st.info("Showing Recurring Deposit Interest Rates (Live from BankBazaar)")
        rd_tables = fetch_rd_tables()
        for title, df in rd_tables.items():
            st.markdown(f"#### {title}")
            st.dataframe(df, use_container_width=True)
    elif option == "savings_account":
        # st.info("Showing Savings Account Interest Rates (Live from BankBazaar)")
        sa_tables = fetch_sa_tables()
        for title, df in sa_tables.items():
            st.markdown(f"#### {title}")
            st.dataframe(df, use_container_width=True)
