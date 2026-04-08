import streamlit as st
from typing import Optional

# External modules (you must implement these)
from auth import login_user
from db import fetch_data


# ---------------------------
# Page Configuration
# ---------------------------
st.set_page_config(
    page_title="Dashboard App",
    page_icon="📊",
    layout="centered",
)


# ---------------------------
# Session State Initialization
# ---------------------------
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None


# ---------------------------
# Login Logic
# ---------------------------
def login(username: str, password: str) -> bool:
    result = login_user(username, password)

    if result["success"]:
        st.session_state.authenticated = True
        st.session_state.username = result["user"]["username"]
        return True
    else:
        st.error(result["message"])
        return False


def logout():
    """
    Logout user and clear session
    """
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()


# ---------------------------
# UI Components
# ---------------------------
def login_page():
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        submitted = st.form_submit_button("Login")

        if submitted:
            if not username or not password:
                st.warning("Please enter both username and password.")
                return

            if login(username, password):
                st.success("Login successful!")
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials.")


def dashboard_page():
    st.title("📊 Dashboard")

    # Welcome message
    st.markdown(f"### Welcome, {st.session_state.username} 👋")

    st.divider()

    # Fetch data section
    if "data" not in st.session_state:
        st.session_state.data = None

    if st.button("Fetch Data from Database"):
        with st.spinner("Fetching data..."):
            try:
                data = fetch_data()
                st.session_state.data = data
                st.success("Data loaded successfully.")
            except Exception as e:
                st.error(f"Error fetching data: {str(e)}")

    # Display data
    if st.session_state.data is not None:
        st.subheader("📋 Data Table")
        st.dataframe(st.session_state.data, use_container_width=True)

    st.divider()

    # Logout button
    if st.button("Logout"):
        logout()


# ---------------------------
# Main App Router
# ---------------------------
def main():
    init_session_state()

    if st.session_state.authenticated:
        dashboard_page()
    else:
        login_page()


# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    main()