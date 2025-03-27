import streamlit as st
from openai import OpenAI

# OpenAI API 키 설정
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

st.title("임시용 챗봇 - 성호중 박범진")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "o3-mini-2025-01-31"

system_message = '''All messages are so important. Take step by step. If you want more information, get it before answer. 
'''

if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    st.session_state.messages = [{"role": "system", "content": system_message}]

for idx, message in enumerate(st.session_state.messages):
    if idx > 0:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("안녕하세요?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
