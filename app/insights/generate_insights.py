# insights
def generate_insights_with_openai(chat_logs):
    # Constructing the conversation context for GPT-3.5-turbo
    conversation_context = [
        {"role": "system", "content": "Analyze the following chat logs and provide the top 5 insights on how students' questioning techniques could be improved:"}]
    for log in chat_logs:
        conversation_context.append({"role": "user", "content": log[2]})
        conversation_context.append({"role": "assistant", "content": log[3]})

    # Sending the context to OpenAI's GPT-3.5-turbo model using the 'client' object
    try:
        response = client.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_context
        )
        return response.choices[0].message['content']
    except Exception as e:
        logging.error(f"Error generating insights with OpenAI: {e}")
        # Consider also logging the conversation context to debug further
        logging.debug(f"Failed conversation context: {conversation_context}")
        return "Error generating insights."
