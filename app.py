import streamlit as st
from groq import Groq

st.title("ChatGPT-like clone with Groq")

groq_api_key = "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"

# Set Groq API key
client = Groq(api_key=groq_api_key)

# Set a default model
if "groq_model" not in st.session_state:
    st.session_state["groq_model"] = "llama-3.3-70b-versatile"  # Example model, adjust as per Groq's models

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Accumulate response from assistant
    assistant_response = ""

    # Get assistant response in a streaming manner and accumulate the chunks
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["groq_model"],
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )

        for chunk in stream:
            assistant_response += chunk["choices"][0]["delta"].get("content", "")

        # Once the full response is accumulated, display it
        st.markdown(assistant_response)

    # Append the full response to the message history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
