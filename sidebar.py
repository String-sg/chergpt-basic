import streamlit as st
from app.chatlog.chatlog_handler import compile_summaries, delete_all_chatlogs, export_chat_logs_to_csv, drop_chatlog_table, fetch_and_batch_chatlogs, generate_summary_for_each_group
from app.instructions.instructions_handler import get_latest_instructions, update_instructions
from app.db.database_connection import  drop_instructions_table, get_app_description, update_app_description, get_app_title, update_app_title
custominstructions_area_height = 300
app_title = get_app_title()
app_description = get_app_description()

def load_summaries():
    # Placeholder function call - replace with actual function logic
    batches = fetch_and_batch_chatlogs()
    group_summaries = generate_summary_for_each_group(batches) 
    final_summary_output = compile_summaries(group_summaries)
    return final_summary_output

def setup_sidebar():
    with st.sidebar:
        st.title("Settings")
        with st.expander("🔑 Admin login"):
            admin_password = st.text_input("Educators only", type="password", key="admin_password")
            if admin_password == st.secrets["ADMIN_PASSWORD"]:
                st.session_state["is_admin"] = True
                st.success("Authenticated as Admin")
            elif admin_password:  
                st.error("Incorrect password")
                st.session_state["is_admin"] = False

    if st.session_state.get("is_admin", False):
        with st.sidebar:
            with st.expander("⚙️ Edit Title"):
                editable_title = st.text_area("This amends title", value=app_title, key="app_title")
                # Button to save the updated app description
                if st.button("Update title", key="save_app_title"):
                    # Update the app description in the database
                    update_app_title(editable_title)
                    st.success("App title updated successfully")
            # Check if the user is an admin to provide editing capability
            # Provide a text area for admins to edit the app description
            with st.expander("⚙️ Edit description"):
                editable_description = st.text_area("This amends text below title", value=app_description, key="app_description")
                # Button to save the updated app description
                if st.button("Update description", key="save_app_description"):
                    # Update the app description in the database
                    update_app_description(editable_description)
                    st.success("App description updated successfully")

            with st.expander("📝 Custom instructions"):
                st.session_state['existing_instructions'] = get_latest_instructions()
                custom_instructions = st.text_area("Edit and save to guide interactions", value=st.session_state['existing_instructions'], height=custominstructions_area_height)

                if st.button("Save Instructions"):
                    update_instructions(custom_instructions)
                    st.success("Instructions updated successfully")
                    st.rerun()

            with st.expander("💬 Chatlog and insights"):
                csv_data = export_chat_logs_to_csv()
                if st.button("View Summary"):
                    # Generate or fetch summaries
                    summaries_text = load_summaries()
                    # Store the summaries in session state to persist the data
                    st.session_state["summaries_text"] = summaries_text
                    st.success("Summaries loaded.")

                    # Immediately display the summaries after loading
                    # Use a modal-like expander to show the summaries
                    st.write(st.session_state["summaries_text"])
                if csv_data:
                    st.download_button(label="Download Chat Logs", data=csv_data, file_name='chat_logs.csv', mime='text/csv',)
                if st.button("Delete All Chat Logs"):
                    delete_all_chatlogs()
            with st.expander("⚠️ Warning: destructive actions"):
                if st.button("Drop chatlog table"):
                    drop_chatlog_table()
                    st.success("Chatlog table dropped")
                    st.rerun()
                if st.button("Drop instructions table"):
                    drop_instructions_table()
                    st.success("Instructions table dropped")
                    st.rerun()


