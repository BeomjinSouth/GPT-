import streamlit as st
from openai import OpenAI

# OpenAI 객체 생성
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

def convert_to_latex(text):
    """일반 텍스트를 LaTeX 형식으로 변환"""
    # [ ... ] 형태를 $...$ 형태로 변환
    text = text.replace('[', '$').replace(']', '$')
    # ( ... ) 형태를 $...$ 형태로 변환
    text = text.replace('(', '$').replace(')', '$')
    return text

st.title("Streaming 챗봇 (LaTeX 지원)")

# 메시지 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 이전 메시지들 표시
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(convert_to_latex(msg["content"]))
        else:
            st.markdown(convert_to_latex(msg["content"]))

# 새로운 메시지가 있을 때 응답 생성
if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""
        
        stream = client.chat.completions.create(
            model="o1-mini",
            messages=st.session_state["messages"],
            stream=True
        )
        
        for response in stream:
            if response.choices[0].delta.content is not None:
                content = response.choices[0].delta.content
                full_response += content
                response_container.markdown(convert_to_latex(full_response))
        
        st.session_state["messages"].append({"role": "assistant", "content": full_response})

# 채팅 입력 (페이지 하단에 위치)
st.markdown("<div style='padding: 3rem;'></div>", unsafe_allow_html=True)  # 여백 추가
user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.rerun()  # experimental_rerun() 대신 rerun() 사용
