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

# Fetch API keys from Streamlit secrets
groq_api_key = "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"
open_cage_api_key = "ab5b5ba90347427cb889b0b4c136e0bf"

st.set_page_config(page_title="Fiscal Forecasting", page_icon=">", layout="wide")
st.title("Relief Bot")

def fetch_location():
    try:
        location = get_geolocation()
        if location:
            return location["coords"]["latitude"], location["coords"]["longitude"]
        else:
            st.warning("Location access denied or unavailable.")
            return None, None
    except Exception as e:
        st.error(f"Error fetching location: {str(e)}")
        return None, None

lat, lon = fetch_location()

if lat and lon:
    try:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={open_cage_api_key}"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200 and data["results"]:
            address = data["results"][0]["formatted"]
            st.success(f"Address: {address}")
        else:
            st.warning("Address not found.")
            address = None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching address: {str(e)}")
        address = None
else:
    address = None

def generate_content(user_question, model, address):
    conversational_memory_length = 5
    memory = ConversationBufferWindowMemory(
        k=conversational_memory_length, memory_key="chat_history", return_messages=True
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    else:
        for message in st.session_state.chat_history:
            memory.save_context({"input": message["human"]}, {"output": message["AI"]})

    groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name=model)

    if user_question:
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=f"""You are a relief bot assisting users with relief efforts. 
                    If the user is asking for help, search the web using the location data ({address}) 
                    and provide relevant disaster-related updates. 
                    Reassure the user that relief assistance is on the way."""
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{user_question}"),
            ]
        )

        conversation = LLMChain(
            llm=groq_chat,
            prompt=prompt,
            verbose=True,
            memory=memory,
        )

        try:
            response = conversation.predict(user_question=user_question)
            message = {"human": user_question, "AI": response}
            st.session_state.chat_history.append(message)
            return response
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return "Sorry, I couldn't generate a response right now."

def main(address):
    model = st.sidebar.selectbox(
        "Choose a model", 
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    )

    user_question = st.text_input("Ask a Question", key="user_question")

    if user_question:
        with st.spinner("Evaluating... Please wait."):
            generated_text = generate_content(user_question, model, address)

        if generated_text:
            st.markdown("### Evaluation Results:")
            st.write(generated_text)

# Main app flow
if __name__ == "__main__":
    main(address)

# Create an agent for the search tool
if address:
    agent = Agent(
        model=Groq(id="llama-3.3-70b-versatile", api_key=groq_api_key),
        tools=[DuckDuckGoTools(), Newspaper4kTools()],
        description="You are a relief bot to search for flood-related news.",
        instructions=[f"Search for flood-related news of today only based on location: {address}."],
        markdown=True,
        show_tool_calls=True,
        add_datetime_to_instructions=True,
    )

    # Display search results with a placeholder to avoid issues with live updates
    result_placeholder = st.empty()
    result = agent.print_response(f"Search result for address: {address}", stream=True)
    result_placeholder.markdown(result)
