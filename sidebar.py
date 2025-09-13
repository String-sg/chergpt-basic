import streamlit as st
from app.chatlog.chatlog_handler import compile_summaries, delete_all_chatlogs, export_chat_logs_to_csv, drop_chatlog_table, fetch_and_batch_chatlogs, generate_summary_for_each_group
from app.instructions.instructions_handler import get_latest_instructions, update_instructions
from app.db.database_connection import  drop_instructions_table, get_app_description, update_app_description, get_app_title, update_app_title
from app.rag.rag_handler import rag_handler
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
        # RAG Status and File Selection (for all users)
        with st.expander("📚 Course Materials"):
            try:
                stats = rag_handler.get_rag_stats()
                if "error" not in stats:
                    if stats['total_chunks'] > 0:
                        rag_status = "✅ Enabled" if st.session_state.get("use_rag", True) else "❌ Disabled"
                        st.write(f"**Status:** {rag_status}")
                        st.caption(f"📊 Database: {stats['total_chunks']} content chunks available")
                        if not st.session_state.get("use_rag", True):
                            st.info("💡 Course material search is currently disabled by an educator")

                        # File Selection Interface for all users
                        if st.session_state.get("user_name"):
                            st.divider()
                            st.write("**📁 Select Materials:**")
                            st.caption("Choose which materials to include in your searches")

                            user_files = rag_handler.get_user_file_selections(st.session_state["user_name"])

                            if user_files:
                                for file_info in user_files:
                                    col1, col2 = st.columns([4, 1])

                                    with col1:
                                        st.write(f"📄 **{file_info['file_name']}**")
                                        st.caption(f"Chunks: {file_info['chunks_count']}")

                                    with col2:
                                        # Use unique key for each checkbox
                                        checkbox_key = f"file_select_{file_info['id']}_{st.session_state['user_name']}"
                                        is_selected = st.checkbox(
                                            "Include",
                                            value=file_info['is_selected'],
                                            key=checkbox_key,
                                            help=f"Include {file_info['file_name']} in searches"
                                        )

                                        # Update selection if changed
                                        if is_selected != file_info['is_selected']:
                                            if rag_handler.update_user_file_selection(
                                                st.session_state["user_name"],
                                                file_info['id'],
                                                is_selected
                                            ):
                                                st.rerun()
                            else:
                                st.info("No materials available for selection.")
                        else:
                            st.info("Please enter your name to select materials.")
                    else:
                        st.warning("⚠️ No course materials found. Contact your educator.")
                else:
                    st.error(f"Database error: {stats['error']}")
            except Exception as e:
                st.error(f"Could not check database status: {e}")
        
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
                    
            with st.expander("📚 RAG Management"):
                # RAG Enable/Disable Toggle (Admin only)
                st.session_state["use_rag"] = st.checkbox(
                    "Enable course material search for all users",
                    value=st.session_state.get("use_rag", True),
                    help="When enabled, the chatbot will search through Economics materials for relevant context when students ask economics-related questions"
                )

                if not st.session_state.get("use_rag", True):
                    st.warning("⚠️ Course material search is currently disabled for all users")

                st.divider()

                # Show detailed RAG statistics
                try:
                    stats = rag_handler.get_rag_stats()
                    if "error" not in stats:
                        st.write("**Database Statistics:**")
                        st.write(f"- Total chunks: {stats['total_chunks']}")
                        st.write(f"- Average chunk length: {stats['avg_chunk_length']} characters")
                        st.write(f"- Chunk length range: {stats['min_chunk_length']} - {stats['max_chunk_length']}")

                        if st.button("🔄 Re-process PDF"):
                            st.info("Run `python process_pdf.py` from the command line to re-process the PDF file")
                    else:
                        st.error(f"Cannot access RAG database: {stats['error']}")
                except Exception as e:
                    st.error(f"RAG system error: {e}")

                st.divider()

                # Ingested Files Management
                st.write("**📁 Ingested Files:**")
                try:
                    ingested_files = rag_handler.get_ingested_files_list()

                    if ingested_files:
                        for file_info in ingested_files:
                            col1, col2, col3 = st.columns([3, 1, 1])

                            with col1:
                                status_icon = {
                                    'completed': '✅',
                                    'processing': '⏳',
                                    'failed': '❌'
                                }.get(file_info['status'], '❓')

                                file_size = rag_handler.format_file_size(file_info['file_size'] or 0)
                                st.write(f"{status_icon} **{file_info['file_name']}**")
                                st.caption(f"Size: {file_size} | Chunks: {file_info['chunks_count']} | Ingested: {file_info['ingested_at'].strftime('%Y-%m-%d %H:%M') if file_info['ingested_at'] else 'Unknown'}")

                                if file_info['error_message']:
                                    st.caption(f"⚠️ {file_info['error_message']}")

                            with col2:
                                if file_info['status'] == 'failed':
                                    if st.button("🔄", key=f"retry_{file_info['id']}", help="Retry processing"):
                                        st.info(f"To retry processing {file_info['file_name']}, run: `python process_pdf.py {file_info['file_path']}`")

                            with col3:
                                if st.button("🗑️", key=f"delete_{file_info['id']}", help="Delete file record"):
                                    if rag_handler.remove_ingested_file(file_info['id']):
                                        st.success(f"Deleted {file_info['file_name']} record")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete file record")
                    else:
                        st.info("No files have been ingested yet. Run `python process_pdf.py <filename>` to ingest PDF files.")

                except Exception as e:
                    st.error(f"Could not load ingested files: {e}")
                    
            with st.expander("⚠️ Warning: destructive actions"):
                if st.button("Drop chatlog table"):
                    drop_chatlog_table()
                    st.success("Chatlog table dropped")
                    st.rerun()
                if st.button("Drop instructions table"):
                    drop_instructions_table()
                    st.success("Instructions table dropped")
                    st.rerun()


