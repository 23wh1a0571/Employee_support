import streamlit as st
import requests

st.set_page_config(page_title="Enterprise HR & IT Support Assistant", page_icon="🤖", layout="wide")

st.title("🤖 Enterprise HR & IT Support Assistant")
st.caption("Powered by FastMCP Tool Architecture & Direct Database Execution")

API_URL = "http://127.0.0.1:8000/api/chat"

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your Enterprise HR & IT Assistant running on pure MCP. How can I assist you today?"}
    ]

# Render Chat History with st.markdown
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input Box
if prompt := st.chat_input("Ask a question (e.g., 'Reset password for EMP101')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Executing FastMCP Tool..."):
            try:
                res = requests.post(API_URL, json={"message": prompt})
                if res.status_code == 200:
                    bot_reply = res.json().get("response", "No response received.")
                else:
                    bot_reply = f"Error {res.status_code}: {res.text}"
            except Exception as e:
                bot_reply = f"Failed to connect to backend server: {str(e)}"

        st.markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})