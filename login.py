import streamlit as st
from auth import verify_user_login
from main import selection_menu

def main():
    # Initialize session state
    session_state = st.session_state

    # Check if user is logged in
    if 'is_logged_in' not in session_state:
        session_state.is_logged_in = False
    
    # If user is not logged in, show login form
    if not session_state.is_logged_in:
        st.title("Login")
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")
        if st.button("Login"):
            if verify_user_login(username, password):
                session_state.is_logged_in = True
                st.success("Login successful!")
            else:
                st.error("Invalid username or password. Please try again.")
    # If user is logged in, show dashboard
    if session_state.is_logged_in:
        selection_menu()

if __name__ == "__main__":
    main()
