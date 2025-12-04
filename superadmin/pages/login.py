"""
Login Page for Streamlit Admin Application
Handles authentication with hardcoded credentials
"""
import streamlit as st
from utils.api_client import api_client


def show_login_page():
    """Display login page"""
    st.title("🔐 Admin Login")
    st.markdown("---")

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Enter your credentials")

        # Login form
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")

            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    with st.spinner("Authenticating..."):
                        # Attempt login
                        result = api_client.login(username, password)

                        if result and "access_token" in result:
                            # Store token and user info in session state
                            st.session_state.token = result["access_token"]
                            st.session_state.authenticated = True
                            st.session_state.username = username

                            # Get user details
                            user_info = api_client.get_current_user()
                            if user_info:
                                st.session_state.user_info = user_info
                                # Handle roles - can be list of strings or list of dicts
                                roles = user_info.get("roles", [])
                                if roles and isinstance(roles[0], dict):
                                    st.session_state.user_roles = [role["name"] for role in roles]
                                else:
                                    st.session_state.user_roles = roles if isinstance(roles, list) else []
                                st.session_state.is_admin = "admin" in st.session_state.user_roles

                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")

        # Show available credentials hint
        with st.expander("ℹ️ Available Credentials", expanded=False):
            st.markdown("""
            **Admin User:**
            - Username: `admin`
            - Password: `admin123`
            - Full access to all features

            **Analyst User:**
            - Username: `analyst1`
            - Password: `analyst123`
            - Limited admin access

            **Viewer User:**
            - Username: `viewer1`
            - Password: `viewer123`
            - Read-only access
            """)

        # Backend status
        st.markdown("---")
        st.caption("🔗 Backend: http://localhost:8000")
        st.caption("Ensure the FastAPI backend is running before logging in")


if __name__ == "__main__":
    show_login_page()
