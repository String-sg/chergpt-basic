
"""
Handles the sidebar UI and admin functionality.
"""
import streamlit as st
import os
from app.chatlog.chatlog_handler import (
    compile_summaries,
    delete_all_chatlogs,
    export_chat_logs_to_csv,
    drop_chatlog_table,
    fetch_and_batch_chatlogs,
    generate_summary_for_each_group
)
from app.instructions.instructions_handler import (
    get_latest_instructions,
    update_instructions
)
from app.db.database_connection import (
    drop_instructions_table,
    get_app_description,
    update_app_description,
    get_app_title,
    update_app_title,
    save_user_prompt,
    get_user_prompts,
    create_session
)

CUSTOM_INSTRUCTIONS_HEIGHT = 300

def load_summaries():
    """Generate and compile chat summaries."""
    batches = fetch_and_batch_chatlogs()
    group_summaries = generate_summary_for_each_group(batches) 
    return compile_summaries(group_summaries)

def setup_admin_authentication():
    """Handle admin authentication in sidebar."""
    with st.expander("🔑 Admin login"):
        admin_password = st.text_input("Educators only", type="password", key="admin_password")
        stored_password = os.environ.get("ADMIN_PASSWORD")
        
        if not stored_password:
            st.error("Admin password not configured. Please set ADMIN_PASSWORD in Replit Secrets.")
            st.session_state["is_admin"] = False
        elif admin_password == stored_password:
            st.session_state["is_admin"] = True
            st.success("Authenticated as Admin")
        elif admin_password:  
            st.error("Incorrect password")
            st.session_state["is_admin"] = False

def setup_admin_controls():
    """Set up admin control panel if authenticated."""
    if not st.session_state.get("is_admin", False):
        return

    with st.expander("⚙️ Edit Title"):
        handle_title_edit()
    
    with st.expander("⚙️ Edit description"):
        handle_description_edit()
    
    with st.expander("📝 Custom instructions"):
        handle_instructions_edit()
    
    with st.expander("💬 Chatlog and insights"):
        handle_chatlog_controls()
    
    with st.expander("⚠️ Warning: destructive actions"):
        handle_destructive_actions()

def handle_title_edit():
    """Handle app title editing."""
    app_title = get_app_title()
    editable_title = st.text_area("This amends title", value=app_title, key="app_title")
    if st.button("Update title", key="save_app_title"):
        update_app_title(editable_title)
        st.success("App title updated successfully")

def handle_description_edit():
    """Handle app description editing."""
    app_description = get_app_description()
    editable_description = st.text_area(
        "This amends text below title",
        value=app_description,
        key="app_description"
    )
    if st.button("Update description", key="save_app_description"):
        update_app_description(editable_description)
        st.success("App description updated successfully")

def handle_instructions_edit():
    """Handle custom instructions editing."""
    st.session_state['existing_instructions'] = get_latest_instructions()
    custom_instructions = st.text_area(
        "Edit and save to guide interactions",
        value=st.session_state['existing_instructions'],
        height=CUSTOM_INSTRUCTIONS_HEIGHT
    )
    if st.button("Save Instructions"):
        update_instructions(custom_instructions)
        st.success("Instructions updated successfully")
        st.rerun()

def handle_chatlog_controls():
    """Handle chatlog viewing and export controls."""
    csv_data = export_chat_logs_to_csv()
    
    if st.button("View Summary"):
        summaries_text = load_summaries()
        st.session_state["summaries_text"] = summaries_text
        st.success("Summaries loaded.")
        st.write(st.session_state["summaries_text"])
        
    if csv_data:
        st.download_button(
            label="Download Chat Logs",
            data=csv_data,
            file_name='chat_logs.csv',
            mime='text/csv'
        )
        
    if st.button("Delete All Chat Logs"):
        delete_all_chatlogs()

def handle_destructive_actions():
    """Handle dangerous database operations."""
    if st.button("Drop chatlog table"):
        drop_chatlog_table()
        st.success("Chatlog table dropped")
        st.rerun()
        
    if st.button("Drop instructions table"):
        drop_instructions_table()
        st.success("Instructions table dropped")
        st.rerun()

def setup_prompt_management():
    """Handle user's custom prompts."""
    if not st.session_state.authenticated_email:
        return
        
    with st.expander("🎯 My Custom Prompts"):
        prompt_name = st.text_input("Prompt Name")
        prompt_content = st.text_area("Prompt Content", height=200)
        
        if st.button("Save Prompt"):
            if prompt_name and prompt_content:
                prompt_id = save_user_prompt(st.session_state.authenticated_email, prompt_name, prompt_content)
                if prompt_id:
                    st.success("Prompt saved!")
                    st.rerun()
                    
        # Display existing prompts
        prompts = get_user_prompts(st.session_state.authenticated_email)
        if prompts:
            st.write("Your Prompts")
            for prompt_id, name, content in prompts:
                with st.expander(name):
                    st.write(content)
                    if st.button(f"Share {name}", key=f"share_{prompt_id}"):
                        session_id = create_session(st.session_state.authenticated_email, prompt_id)
                        if session_id:
                            share_url = f"{os.getenv('BASE_URL', 'https://chergpt.replit.app')}/chat?session={session_id}"
                            st.code(share_url)
                            st.info("Share this URL to let others use your prompt!")

def setup_sidebar():
    """Main sidebar setup function."""
    with st.sidebar:
        st.title("Settings")
        setup_prompt_management()
        setup_admin_authentication()
        setup_admin_controls()
