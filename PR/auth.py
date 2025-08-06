import streamlit as st
from database import authenticate_user, register_user, validate_email, validate_phone, check_email_exists, get_next_user_id

def login_page():
    """Display login page with signup option"""

    # Page Title
    st.markdown('<h1 class="main-header">Expense Tracker</h1>', unsafe_allow_html=True)
    
    # Login / Sign Up Tabs
    tab1, tab2 = st.tabs([" Login", " Sign Up"])

    # ───────── LOGIN TAB ─────────
    with tab1:
        with st.container():
            st.markdown("""
                <style>
                    .stForm {
                        max-width: 35rem;
                        margin: 80px auto;
                        margin-top: 2rem;
                        padding: 2rem;
                        padding-top:4rem;
                        padding-bottom: 4rem;
                        border-radius: 12px;
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                    }

                    .stTextInput{
                        padding: 9px;
                        width: 90%;
                        margin-left:1rem;
                        font-size: 14px;
                        color: #333;
                    }

                    .main-header {
                        text-align: center;
                        margin-bottom: 2rem;
                        font-size: 2.5rem;
                    }
                    .login_text {
                        text-align: center;
                        margin-bottom: 1rem;    
                    }    
                </style>
            """, unsafe_allow_html=True)

            st.markdown('<div class="login-box">', unsafe_allow_html=True)

            with st.form("login_form"):
                st.markdown('<h2 class="login_text">Login to your account</h2>', unsafe_allow_html=True)
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")

                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submit_button = st.form_submit_button("🚀 Login", use_container_width=True)

                if submit_button:
                    if email and password:
                        user = authenticate_user(email, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user_id = user[0]
                            st.session_state.user_name = user[1]
                            st.success("Login successful! Welcome back!")
                            st.rerun()
                        else:
                            st.error("Invalid email or password. Please try again.")
                    else:
                        st.error("Please fill in all fields.")

            st.markdown("</div>", unsafe_allow_html=True)

    # ───────── SIGN UP TAB ─────────
    with tab2:
        with st.container():
            # Optional: add signup-specific styling
            st.markdown("""
                <style>
                    .stNumberInput{
                        padding: 10px;
                        width: 90%;
                        margin-left:1rem;
                        font-size: 14px;
                        color: #333;
                    }
                    .signup_text{
                        text-align: center;
                        margin-bottom: 1rem;    
                    }    
                </style>
            """, unsafe_allow_html=True)

            st.markdown('<div class="signup-container">', unsafe_allow_html=True)

            with st.form("signup_form"):
                st.markdown('<h2 class="signup_text">Create Account</h2>', unsafe_allow_html=True)
                name = st.text_input("Full Name", placeholder="Enter your full name")
                age = st.number_input("Age", min_value=13, max_value=120, value=20)
                email = st.text_input("Email", placeholder="Enter your email address")
                password = st.text_input("Password", type="password", placeholder="Create a password (min 6 characters)")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                phone_number = st.text_input("Phone Number", placeholder="Enter your phone number")

                # Password strength indicator
                if password:
                    strength = 0
                    if len(password) >= 6: strength += 1
                    if any(c.isupper() for c in password): strength += 1
                    if any(c.islower() for c in password): strength += 1
                    if any(c.isdigit() for c in password): strength += 1
                    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password): strength += 1

                    strength_labels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
                    strength_colors = ["red", "orange", "yellow", "lightgreen", "green"]

                    if strength > 0:
                        st.markdown(
                            f"**Password Strength:** <span style='color: {strength_colors[strength-1]}'>{strength_labels[strength-1]}</span>",
                            unsafe_allow_html=True
                        )

                agree_terms = st.checkbox("I agree to the Terms and Conditions")

                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    signup_button = st.form_submit_button("Create Account", use_container_width=True)

                if signup_button:
                    # Validate inputs
                    if not name or not email or not password or not confirm_password or not phone_number:
                        st.error("Please fill in all required fields.")
                    elif len(name.strip()) < 2:
                        st.error("Name must be at least 2 characters long.")
                    elif not validate_email(email):
                        st.error("Please enter a valid email address.")
                    elif password != confirm_password:
                        st.error("Passwords do not match. Please try again.")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif not validate_phone(phone_number):
                        st.error("Please enter a valid phone number (10-15 digits).")
                    elif not agree_terms:
                        st.error("Please agree to the Terms and Conditions.")
                    elif check_email_exists(email):
                        st.error("Email already exists. Please use a different email or login.")
                    else:
                        success = register_user(name.strip(), age, email.lower(), password, phone_number)
                        if success:
                            st.success("Account created successfully! You can now login.")
                            st.balloons()

                            st.markdown("### Account Details")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Name", name.strip())
                                st.metric("Email", email.lower())
                                st.metric("Phone", phone_number)
                            with col2:
                                st.metric("Age", age)
                                st.metric("User ID", get_next_user_id() - 1)
                                st.metric("Status", "Active")

                            st.info("You can now login with your email and password!")
                        else:
                            st.error("Failed to create account. Please try again.")

            st.markdown("</div>", unsafe_allow_html=True)