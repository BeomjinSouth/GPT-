import streamlit as st
from openai import OpenAI

# OpenAI API 키 설정
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

st.title("임시용 챗봇 - 성호중 박범진")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "o3-mini-2025-01-31"

system_message = '''All messages are so important. Take step by step. If you want more information, get it before answer.
너는 중학교 1학년 학생들을 대상으로 수학 문제 풀이 과정을 
'''

# 챗봇 새로고침 버튼 (클릭 시 메시지를 초기화)
if st.button("챗봇 새로고침"):
    st.session_state.messages = [{"role": "system", "content": system_message}]

if "messages" not in st.session_state:
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
        full_response = ""
        response = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        )
        full_response += response.choices[0].message.content
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
