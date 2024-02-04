# Admin panel for custom instructions

if st.session_state.get("is_admin"):
    with st.sidebar:
        st.title("Admin Panel")
        existing_instructions = get_latest_instructions()
        custom_instructions = st.text_area(
            "Custom Instructions", value=existing_instructions,
            height=custominstructions_area_height)

        if st.button("Save Instructions"):
            update_instructions(custom_instructions)
            st.success("Instructions updated successfully")
            st.rerun()
        csv_data = export_chat_logs_to_csv()
        if csv_data:
            st.download_button(
                label="Download Chat Logs",
                data=csv_data,
                file_name='chat_logs.csv',
                mime='text/csv',
            )
        if st.button("Delete All Chat Logs"):
            delete_all_chatlogs()

        if st.button("Generate Insights from Recent Chats"):
            recent_chats = fetch_recent_chat_logs(1)  # Last hour
            print(recent_chats)
            if recent_chats:
                insights = generate_insights_with_openai(recent_chats)
                st.write(insights)
            else:
                st.write("No recent chats to analyze.")
