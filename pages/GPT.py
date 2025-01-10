import streamlit as st
from openai import OpenAI
import re

# OpenAI 객체 생성
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

def process_latex(text):
    """LaTeX 수식을 Streamlit markdown으로 변환"""
    # 인라인 수식 처리 ($...$ 형태)
    text = re.sub(r'\$(.+?)\$', r'$\1$', text)
    # 디스플레이 수식 처리 ($$....$$ 형태)
    text = re.sub(r'\$\$(.*?)\$\$', r'$$\1$$', text, flags=re.DOTALL)
    return text

st.title("Streaming 챗봇 (LaTeX 지원)")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 사용자 입력
user_input = st.text_input("메시지를 입력하세요:")

if st.button("전송") and user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})

# 이전 메시지들 표시
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(process_latex(msg["content"]))
        else:
            st.write(msg["content"])

# 새로운 메시지가 있을 때 응답 생성
if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""
        
        # 스트리밍 응답 생성
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=st.session_state["messages"],
            stream=True
        )
        
        for response in stream:
            if response.choices[0].delta.content is not None:
                content = response.choices[0].delta.content
                full_response += content
                # 실시간으로 LaTeX 처리된 텍스트 출력
                response_container.markdown(process_latex(full_response))
        
        # 최종 응답 저장
        st.session_state["messages"].append({"role": "assistant", "content": full_response})
