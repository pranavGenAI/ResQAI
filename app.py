import streamlit as st
from streamlit_js_eval import get_geolocation
import requests
from groq import Groq
from langchain.chains import LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools

# Page config
st.set_page_config(
    page_title="Relief Bot",
    page_icon="🤖",
    layout="centered"
)

# Custom CSS for chat interface
st.markdown("""
    <style>
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e6f3ff;
        border: 1px solid #b3d9ff;
    }
    .bot-message {
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
    }
    .message-content {
        margin-top: 0.5rem;
    }
    .stTextInput>div>div>input {
        border-radius: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'location_fetched' not in st.session_state:
    st.session_state.location_fetched = False

# API keys
groq_api_key = "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"
open_cage_api_key = "ab5b5ba90347427cb889b0b4c136e0bf"

def fetch_location():
    if not st.session_state.location_fetched:
        try:
            location = get_geolocation()
            if location:
                lat = location["coords"]["latitude"]
                lon = location["coords"]["longitude"]
                url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={open_cage_api_key}"
                response = requests.get(url)
                data = response.json()
                
                if response.status_code == 200 and data["results"]:
                    address = data["results"][0]["formatted"]
                    st.session_state.address = address
                    st.session_state.location_fetched = True
                    return address
            return None
        except Exception as e:
            st.error(f"Error fetching location: {str(e)}")
            return None
    return st.session_state.get('address')

def generate_response(user_input, model, address):
    memory = ConversationBufferWindowMemory(
        k=5,
        memory_key="chat_history",
        return_messages=True
    )
    
    # Load chat history into memory
    for message in st.session_state.messages:
        if message["role"] == "user":
            memory.save_context(
                {"input": message["content"]},
                {"output": st.session_state.messages[st.session_state.messages.index(message) + 1]["content"]}
            )
    
    groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name=model)
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are a friendly and empathetic relief bot assisting users with disaster-related information and support.
        Current location: {address}
        
        Guidelines:
        - Provide relevant and up-to-date disaster-related information
        - Be reassuring and supportive while remaining factual
        - Include specific details about available resources and assistance
        - Keep responses concise but informative
        - Use a warm, compassionate tone"""),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{input}")
    ])
    
    chain = LLMChain(
        llm=groq_chat,
        prompt=prompt,
        verbose=True,
        memory=memory,
    )
    
    try:
        return chain.predict(input=user_input)
    except Exception as e:
        return f"I apologize, but I'm having trouble generating a response right now. Error: {str(e)}"

def main():
    st.title("🤖 Relief Bot")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        model = st.selectbox(
            "Choose a model",
            ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            index=0
        )
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.location_fetched = False
            st.rerun()
    
    # Get location
    address = fetch_location()
    if address:
        st.sidebar.success(f"📍 Location: {address}")
    else:
        st.sidebar.warning("⚠️ Location access required for local updates")
        return
    
    # Chat interface
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="chat-message user-message">
                        <div><strong>You</strong></div>
                        <div class="message-content">{message["content"]}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-message bot-message">
                        <div><strong>Relief Bot</strong></div>
                        <div class="message-content">{message["content"]}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # User input
    user_input = st.text_input("Type your message here...", key="user_input")
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Generate and add bot response
        with st.spinner("Thinking..."):
            bot_response = generate_response(user_input, model, address)
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
        
        # Clear input and rerun to update chat
        st.rerun()

    # Search tool section
    if len(st.session_state.messages) > 0:
        with st.expander("🔍 Local Updates", expanded=False):
            try:
                agent = Agent(
                    model=Groq(id="llama-3.3-70b-versatile", api_key=groq_api_key),
                    tools=[DuckDuckGoTools(), Newspaper4kTools()],
                    description="You are a relief bot searching for local disaster-related news.",
                    instructions=[f"Search for disaster-related news of today only based on location: {address}"],
                    markdown=True,
                    show_tool_calls=False,
                    add_datetime_to_instructions=True,
                )
                
                search_results = agent.run(f"Search for recent disaster updates in: {address}")
                st.markdown(search_results)
            except Exception as e:
                st.error(f"Error fetching updates: {str(e)}")

if __name__ == "__main__":
    main()
