import streamlit as st


def setup_sidebar():
    with st.sidebar:
        st.title("Settings")
        with st.expander("Admin config"):
            admin_password = st.text_input(
                "Enter Admin Password", type="password")

            if admin_password == st.secrets["ADMIN_PASSWORD"]:
                st.session_state["is_admin"] = True
                st.success("Authenticated as Admin")
            elif admin_password:  # Only display message if something was entered
                st.error("Incorrect password")
                st.session_state["is_admin"] = False
    pass
