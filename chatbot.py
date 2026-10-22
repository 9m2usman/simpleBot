# Step 3: the chatbot website.   Run:  streamlit run chatbot.py
import requests
import streamlit as st

from bot_core import STORE_NAME, TRANSLATOR_KEY, get_reply, to_urdu, using_azure

st.set_page_config(page_title=f"{STORE_NAME} Assistant", page_icon="🛍️")
st.title(f"🛍️ {STORE_NAME} Assistant")
st.caption("I answer questions about orders, delivery, payments and returns. "
           "I am a bot, not a person.")

QUICK_QUESTIONS = [
    "How can I track my order?",
    "What is your return policy?",
    "How long does delivery take?",
    "Which payment methods do you accept?",
    "I want to talk to a human agent.",
]

with st.sidebar:
    st.header("Quick questions")
    quick = None
    for q in QUICK_QUESTIONS:
        if st.button(q):
            quick = q
    st.divider()
    urdu = st.toggle("Answer in Urdu", value=False, disabled=not TRANSLATOR_KEY)
    if st.button("Clear chat"):
        st.session_state.chat = []
    st.caption("Search engine: " + ("Azure AI Search" if using_azure()
                                    else "offline demo mode (no Azure keys in .env)"))

if "chat" not in st.session_state:
    st.session_state.chat = []

# show the earlier messages
for role, text in st.session_state.chat:
    st.chat_message(role).write(text)

if not st.session_state.chat:
    st.chat_message("assistant").write(
        f"Hello! Welcome to {STORE_NAME}. Ask me about orders, delivery, payments, "
        "returns or your account. You can also tap a quick question on the left.")

question = st.chat_input("Type your question, e.g. Where is my order?") or quick
if question:
    st.chat_message("user").write(question)
    try:
        reply = get_reply(question)
        answer = reply["answer"]
        if urdu:
            answer = to_urdu(answer)
        if reply["found"] and reply["related"]:
            answer += "\n\n_You may also ask: " + " | ".join(reply["related"]) + "_"
    except requests.RequestException:
        answer = "Sorry, I cannot reach the search service right now. Please try again in a minute."
    st.chat_message("assistant").write(answer)
    st.session_state.chat += [("user", question), ("assistant", answer)]
