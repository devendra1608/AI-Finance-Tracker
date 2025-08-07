import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

def get_loan_data(loan_type):
    """
    Scrape loan data from BankBazaar based on loan type
    """
    loan_urls = {
        "car_loan": "https://www.bankbazaar.com/car-loan.html",
        "personal_loan": "https://www.bankbazaar.com/personal-loan.html", 
        "home_loan": "https://www.bankbazaar.com/home-loan.html",
        "two_wheeler_loan": "https://www.bankbazaar.com/two-wheeler-loan.html",
        "used_car_loan": "https://www.bankbazaar.com/used-car-loan.html",
        "education_loan": "https://www.bankbazaar.com/education-loan.html"
    }
    
    url = loan_urls.get(loan_type)
    if not url:
        return None
    
    try:
        # Add headers to mimic a real browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract loan comparison table - more specific targeting
        loan_data = []
        
        # Look for specific loan comparison tables
        # BankBazaar typically uses specific classes or IDs for loan tables
        loan_tables = soup.find_all('table', class_=lambda x: x and any(keyword in x.lower() for keyword in ['loan', 'rate', 'comparison', 'bank']))
        
        # If no specific loan tables found, look for tables with loan-related content
        if not loan_tables:
            all_tables = soup.find_all('table')
            for table in all_tables:
                # Check if table contains loan-related keywords
                table_text = table.get_text().lower()
                if any(keyword in table_text for keyword in ['interest rate', 'bank', 'loan', 'tenure', 'emi']):
                    loan_tables.append(table)
        
        for table in loan_tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    bank_name = cells[0].get_text(strip=True)
                    interest_rate = cells[1].get_text(strip=True)
                    tenure = cells[2].get_text(strip=True)
                    
                    # Validate that this looks like loan data
                    if (bank_name and 
                        interest_rate and 
                        ('%' in interest_rate or 'rate' in interest_rate.lower()) and
                        any(bank in bank_name.lower() for bank in ['bank', 'finance', 'capital', 'sbi', 'hdfc', 'icici', 'axis', 'canara', 'pnb', 'union', 'idfc', 'kotak', 'yes', 'tata', 'standard', 'indusind', 'idbi', 'bajaj', 'hero', 'tvs', 'mahindra', 'iifl', 'hdbfs'])):
                        
                        loan_data.append({
                            'Bank Name': bank_name,
                            'Interest Rate': interest_rate,
                            'Tenure': tenure
                        })
        
        # If still no data, try to extract from specific loan sections
        if not loan_data:
            # Look for loan comparison sections
            loan_sections = soup.find_all(['div', 'section'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['loan', 'comparison', 'rate', 'bank']))
            
            for section in loan_sections:
                # Look for structured loan information
                loan_items = section.find_all(['div', 'p'], string=lambda text: text and '%' in text and any(bank in text.lower() for bank in ['bank', 'finance', 'capital']))
                
                for item in loan_items:
                    text = item.get_text(strip=True)
                    # Parse loan information from text
                    if '%' in text and any(bank in text.lower() for bank in ['sbi', 'hdfc', 'icici', 'axis', 'canara']):
                        # Try to extract structured information
                        parts = text.split()
                        for i, part in enumerate(parts):
                            if '%' in part and i > 0:
                                bank_name = ' '.join(parts[:i])
                                interest_rate = part
                                loan_data.append({
                                    'Bank Name': bank_name,
                                    'Interest Rate': interest_rate,
                                    'Tenure': 'Contact Bank'
                                })
                                break
        
        # Filter out any non-loan related entries
        filtered_loan_data = []
        for item in loan_data:
            bank_name = item['Bank Name'].lower()
            interest_rate = item['Interest Rate'].lower()
            
            # Skip if it doesn't look like loan data
            if (any(keyword in bank_name for keyword in ['bank', 'finance', 'capital', 'sbi', 'hdfc', 'icici', 'axis', 'canara', 'pnb', 'union', 'idfc', 'kotak', 'yes', 'tata', 'standard', 'indusind', 'idbi', 'bajaj', 'hero', 'tvs', 'mahindra', 'iifl', 'hdbfs']) and
                ('%' in interest_rate or 'rate' in interest_rate)):
                filtered_loan_data.append(item)
        
        return filtered_loan_data
        
    except Exception as e:
        st.error(f"Error fetching loan data: {str(e)}")
        return None

def get_static_loan_data(loan_type):
    """
    Get static loan data based on loan type (fallback when web scraping fails)
    """
    loan_data = {
        "car_loan": [
            {"Bank Name": "State Bank of India", "Interest Rate": "8.90% p.a.", "Tenure": "Up to 7 years"},
            {"Bank Name": "Indian Overseas Bank", "Interest Rate": "7.80% p.a.", "Tenure": "Up to 7 years"},
            {"Bank Name": "IDFC First Bank", "Interest Rate": "9.99% p.a.", "Tenure": "Up to 10 years"},
            {"Bank Name": "Canara Bank", "Interest Rate": "8.05% p.a.", "Tenure": "Up to 7 years"},
            {"Bank Name": "HDFC Bank", "Interest Rate": "9.40% p.a.", "Tenure": "Up to 7 years"},
            {"Bank Name": "ICICI Bank", "Interest Rate": "9.10% p.a.", "Tenure": "Up to 7 years"},
            {"Bank Name": "Axis Bank", "Interest Rate": "8.90% p.a.", "Tenure": "Up to 7 years"},
            {"Bank Name": "Bank of Baroda", "Interest Rate": "8.75% p.a.", "Tenure": "Up to 7 years"}
        ],
        "personal_loan": [
            {"Bank Name": "SBI Personal Loan", "Interest Rate": "10.30% p.a.", "Tenure": "Up to 6 years", "Max Amount": "₹30L", "Best For": "Different income groups"},
            {"Bank Name": "HDFC Personal Loan", "Interest Rate": "10.90%–24% p.a.", "Tenure": "Up to 5 years", "Max Amount": "₹40L", "Best For": "Self-employed"},
            {"Bank Name": "Kotak Mahindra Personal Loan", "Interest Rate": "10.99% p.a.", "Tenure": "Up to 5 years", "Max Amount": "₹40L", "Best For": "Fast processing"},
            {"Bank Name": "Yes Bank Personal Loan", "Interest Rate": "11.25%–21% p.a.", "Tenure": "Up to 6 years", "Max Amount": "₹40L", "Best For": "Quick approval"},
            {"Bank Name": "Union Bank of India Personal Loan", "Interest Rate": "11.25%–14.95% p.a.", "Tenure": "Up to 5 years", "Max Amount": "₹15L", "Best For": "First-time borrowers"},
            {"Bank Name": "Axis Bank Personal Loan", "Interest Rate": "10.40% p.a.", "Tenure": "Up to 7 years", "Max Amount": "₹40L", "Best For": "Minimal docs"},
            {"Bank Name": "Tata Capital Personal Loan", "Interest Rate": "11.99% p.a.", "Tenure": "Up to 6 years", "Max Amount": "₹35L", "Best For": "Flexible rates"},
            {"Bank Name": "Standard Chartered Personal Loan", "Interest Rate": "11.49% p.a.", "Tenure": "Up to 5 years", "Max Amount": "₹50L", "Best For": "Short-term needs"},
            {"Bank Name": "IDFC First Personal Loan", "Interest Rate": "9.99% p.a.", "Tenure": "Up to 5 years", "Max Amount": "₹10L", "Best For": "Top-up loans"},
            {"Bank Name": "IIFL Personal Loan", "Interest Rate": "12.75% p.a.", "Tenure": "42 months", "Max Amount": "₹5L", "Best For": "Easy eligibility"},
            {"Bank Name": "HDBFS Personal Loan", "Interest Rate": "36% p.a.", "Tenure": "Up to 5 years", "Max Amount": "₹20L", "Best For": "Offers"},
            {"Bank Name": "PNB Personal Loan", "Interest Rate": "11.40% p.a.", "Tenure": "Up to 6 years", "Max Amount": "₹20L", "Best For": "Affordable rates"},
            {"Bank Name": "IndusInd Bank Personal Loan", "Interest Rate": "10.49% p.a.", "Tenure": "Up to 6 years", "Max Amount": "₹50L", "Best For": "Flexible tenure"},
            {"Bank Name": "IDBI Bank Personal Loan", "Interest Rate": "Contact Bank", "Tenure": "Up to 5 years", "Max Amount": "₹5L", "Best For": "Simple process"}
        ],
        "home_loan": [
            {"Bank Name": "State Bank of India", "Interest Rate": "8.40% p.a.", "Tenure": "Up to 30 years"},
            {"Bank Name": "HDFC Bank", "Interest Rate": "8.75% p.a.", "Tenure": "Up to 30 years"},
            {"Bank Name": "ICICI Bank", "Interest Rate": "8.85% p.a.", "Tenure": "Up to 30 years"},
            {"Bank Name": "Axis Bank", "Interest Rate": "8.75% p.a.", "Tenure": "Up to 30 years"},
            {"Bank Name": "Bank of Baroda", "Interest Rate": "8.40% p.a.", "Tenure": "Up to 30 years"},
            {"Bank Name": "Canara Bank", "Interest Rate": "8.40% p.a.", "Tenure": "Up to 30 years"},
            {"Bank Name": "Punjab National Bank", "Interest Rate": "8.40% p.a.", "Tenure": "Up to 30 years"},
            {"Bank Name": "Union Bank of India", "Interest Rate": "8.40% p.a.", "Tenure": "Up to 30 years"}
        ],
        "two_wheeler_loan": [
            {"Bank Name": "HDFC Bank", "Interest Rate": "12.99% p.a.", "Tenure": "Up to 3 years"},
            {"Bank Name": "ICICI Bank", "Interest Rate": "13.99% p.a.", "Tenure": "Up to 3 years"},
            {"Bank Name": "Axis Bank", "Interest Rate": "12.99% p.a.", "Tenure": "Up to 3 years"},
            {"Bank Name": "Bajaj Auto Finance", "Interest Rate": "12.99% p.a.", "Tenure": "Up to 3 years"},
            {"Bank Name": "Hero FinCorp", "Interest Rate": "13.99% p.a.", "Tenure": "Up to 3 years"},
            {"Bank Name": "TVS Credit", "Interest Rate": "13.99% p.a.", "Tenure": "Up to 3 years"},
            {"Bank Name": "Mahindra Finance", "Interest Rate": "13.99% p.a.", "Tenure": "Up to 3 years"},
            {"Bank Name": "Kotak Mahindra Bank", "Interest Rate": "12.99% p.a.", "Tenure": "Up to 3 years"}
        ],
        "used_car_loan": [
            {"Bank Name": "HDFC Bank", "Interest Rate": "13.99% p.a.", "Tenure": "Up to 5 years"},
            {"Bank Name": "ICICI Bank", "Interest Rate": "14.99% p.a.", "Tenure": "Up to 5 years"},
            {"Bank Name": "Axis Bank", "Interest Rate": "13.99% p.a.", "Tenure": "Up to 5 years"},
            {"Bank Name": "State Bank of India", "Interest Rate": "14.15% p.a.", "Tenure": "Up to 5 years"},
            {"Bank Name": "Canara Bank", "Interest Rate": "14.05% p.a.", "Tenure": "Up to 5 years"},
            {"Bank Name": "Bank of Baroda", "Interest Rate": "13.75% p.a.", "Tenure": "Up to 5 years"},
            {"Bank Name": "Kotak Mahindra Bank", "Interest Rate": "13.99% p.a.", "Tenure": "Up to 5 years"},
            {"Bank Name": "Tata Capital", "Interest Rate": "14.99% p.a.", "Tenure": "Up to 5 years"}
        ],
        "education_loan": [
            {"Bank Name": "State Bank of India", "Interest Rate": "8.15% p.a.", "Tenure": "Up to 15 years"},
            {"Bank Name": "HDFC Bank", "Interest Rate": "8.75% p.a.", "Tenure": "Up to 15 years"},
            {"Bank Name": "ICICI Bank", "Interest Rate": "8.85% p.a.", "Tenure": "Up to 15 years"},
            {"Bank Name": "Axis Bank", "Interest Rate": "8.75% p.a.", "Tenure": "Up to 15 years"},
            {"Bank Name": "Canara Bank", "Interest Rate": "8.40% p.a.", "Tenure": "Up to 15 years"},
            {"Bank Name": "Bank of Baroda", "Interest Rate": "8.40% p.a.", "Tenure": "Up to 15 years"},
            {"Bank Name": "Punjab National Bank", "Interest Rate": "8.40% p.a.", "Tenure": "Up to 15 years"},
            {"Bank Name": "Union Bank of India", "Interest Rate": "8.40% p.a.", "Tenure": "Up to 15 years"}
        ]
    }
    
    return loan_data.get(loan_type, [])

def loan_comparison_page():
    """
    Main loan comparison page
    """
    st.markdown(f'<h1 class="main-header"> Loan Comparison </h1>', unsafe_allow_html=True)
    
    # Loan type selection
    st.markdown("###  Select Loan Type")
    
    loan_types = {
        "car_loan": "Car Loan",
        "personal_loan": "Personal Loan", 
        "home_loan": "Home Loan",
        "two_wheeler_loan": " Two Wheeler Loan",
        "used_car_loan": " Used Car Loan",
        "education_loan": " Education Loan"
    }
    
    selected_loan = st.selectbox(
        "Choose the type of loan you want to compare:",
        options=list(loan_types.keys()),
        format_func=lambda x: loan_types[x]
    )
    

    
    # Compare button
    if st.button("🔍 Compare Loans", use_container_width=True):
        # Try to get live data first, fallback to static data seamlessly
        loan_data = get_loan_data(selected_loan)
        
        if not loan_data or len(loan_data) < 3:
            loan_data = get_static_loan_data(selected_loan)
        
        if loan_data:
            st.success(f"✅ Found {len(loan_data)} loan options!")
            
            # Display loan comparison table
            st.markdown(f"###  {loan_types[selected_loan]} Comparison")
            
            df = pd.DataFrame(loan_data)
            
            # Configure columns based on loan type
            if selected_loan == "personal_loan":
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "Bank Name": st.column_config.TextColumn(" Bank Name", width="medium"),
                        "Interest Rate": st.column_config.TextColumn(" Interest Rate", width="medium"),
                        "Tenure": st.column_config.TextColumn(" Tenure", width="medium"),
                        "Max Amount": st.column_config.TextColumn(" Max Amount", width="medium"),
                        "Best For": st.column_config.TextColumn(" Best For", width="medium")
                    }
                )
            else:
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "Bank Name": st.column_config.TextColumn(" Bank Name", width="medium"),
                        "Interest Rate": st.column_config.TextColumn(" Interest Rate", width="medium"),
                        "Tenure": st.column_config.TextColumn(" Tenure", width="medium")
                    }
                )
            
            
            
            
            
            
        else:
            st.error("❌ Unable to fetch loan data. Please try again later.")

if __name__ == "__main__":
    loan_comparison_page()
