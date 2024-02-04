import streamlit as st
from app.chatlog.chatlog_handler import delete_all_chatlogs, export_chat_logs_to_csv
from app.instructions.instructions_handler import get_latest_instructions, update_instructions

custominstructions_area_height = 300

def setup_sidebar():
    with st.sidebar:
        st.title("Settings")
        with st.expander("Admin config"):
            admin_password = st.text_input("Enter Admin Password", type="password", key="admin_password")
            if admin_password == st.secrets["ADMIN_PASSWORD"]:
                st.session_state["is_admin"] = True
                st.success("Authenticated as Admin")
            elif admin_password:  
                st.error("Incorrect password")
                st.session_state["is_admin"] = False

    if st.session_state.get("is_admin", False):
        with st.sidebar:
            st.title("Admin Panel")
            st.session_state['existing_instructions'] = get_latest_instructions()
            custom_instructions = st.text_area("Custom Instructions", value=st.session_state['existing_instructions'], height=custominstructions_area_height)

            if st.button("Save Instructions"):
                update_instructions(custom_instructions)
                st.success("Instructions updated successfully")
                st.experimental_rerun()
            
            csv_data = export_chat_logs_to_csv()
            if csv_data:
                 st.download_button(label="Download Chat Logs", data=csv_data, file_name='chat_logs.csv', mime='text/csv',)
            if st.button("Delete All Chat Logs"):
                 delete_all_chatlogs()

