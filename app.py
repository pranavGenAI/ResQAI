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


# Fetch API keys from Streamlit secrets
gemini_api_key = st.secrets["GEMINI_API_KEY"]
groq_api_key = st.secrets["GROQ_API_KEY"]  # Assuming you've stored this in secrets

st.set_page_config(page_title="Fiscal Forecasting", page_icon=">", layout="wide")
st.title("Get User Location in Streamlit")

# Fetch user location
location = get_geolocation()

if location:
    lat, lon = location["coords"]["latitude"], location["coords"]["longitude"]
else:
    lat, lon = None, None
    st.warning("Click the button and allow location access.")

# Get coordinates
if lat is not None and lon is not None:
    api_key = "ab5b5ba90347427cb889b0b4c136e0bf"  # Replace with your OpenCage API key
    url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={api_key}"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200 and data["results"]:
        address = data["results"][0]["formatted"]
        st.success(f"Address: {address}")
    else:
        address = None
        st.warning("Address not found.")
else:
    address = None

# Sidebar - Model Selection
st.sidebar.image(
    "https://www.vgen.it/wp-content/uploads/2021/04/logo-accenture-ludo.png", width=70
)
st.sidebar.title("Model Selection")


def generate_content(user_question, model, address):
    """Generates a response based on user input and location data."""
    conversational_memory_length = 5
    memory = ConversationBufferWindowMemory(
        k=conversational_memory_length, memory_key="chat_history", return_messages=True
    )

    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    else:
        for message in st.session_state.chat_history:
            memory.save_context({"input": message["human"]}, {"output": message["AI"]})

    # Initialize Groq chat model
    groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name=model)

    if user_question:
        # Create a prompt with user location context
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

        # Generate AI response
        conversation = LLMChain(
            llm=groq_chat,
            prompt=prompt,
            verbose=True,
            memory=memory,
        )

        response = conversation.predict(user_question=user_question)
        message = {"human": user_question, "AI": response}
        st.session_state.chat_history.append(message)

        return response


def main(address):
    """Main function to run the Streamlit app."""
    st.markdown("")
    
    model = st.sidebar.selectbox(
        "Choose a model",
        ["llama-3.1-70b-versatile", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
    )

    generated_text = ""

    user_question = st.text_input("Ask a Question", key="user_question")

    if user_question:
        with st.spinner("Evaluating..."):
            generated_text = generate_content(user_question, model, address)

        if generated_text:
            st.markdown("### Evaluation Results:")
            st.write(generated_text)


if __name__ == "__main__":
    main(address)
