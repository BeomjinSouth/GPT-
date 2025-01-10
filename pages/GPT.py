import streamlit as st
from openai import OpenAI

# OpenAI 객체 생성 (실제 API 키로 교체)
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

st.title("Streaming 예시")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 사용자 입력
user_input = st.text_input("메시지를 입력하세요:")
if st.button("전송") and user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})

# 기존 메시지 출력
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:  # assistant
        with st.chat_message("assistant"):
            st.write(msg["content"])

# 마지막 메시지가 사용자 메시지라면, 스트리밍 요청
if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        # 스트리밍 생성
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state["messages"],
            stream=True,
        )

        for chunk in stream:
            delta = chunk["choices"][0]["delta"]
            content = delta.get("content", "")
            if content:
                full_response += content
                # 스트리밍 출력
                response_container.write(full_response)

        # 최종 응답 저장
        st.session_state["messages"].append({"role": "assistant", "content": full_response})
