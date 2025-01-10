import streamlit as st
from openai import OpenAI
import re

# OpenAI 객체 생성
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

def setup_latex_support():
    """LaTeX 지원을 위한 MathJax 설정"""
    st.markdown("""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.9/MathJax.js?config=TeX-MML-AM_CHTML">
        </script>
        """, unsafe_allow_html=True)

def format_message(text):
    """메시지 포맷팅 및 LaTeX 수식 처리"""
    # 여러 줄 수식 ($$...$$) 처리
    text = re.sub(r'\$\$(.*?)\$\$', r'\\[\1\\]', text, flags=re.DOTALL)
    
    # 줄바꿈 보존
    paragraphs = text.split('\n')
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        if paragraph.strip():
            # 불릿 포인트 처리
            if paragraph.strip().startswith('*'):
                paragraph = paragraph.strip()
            formatted_paragraphs.append(paragraph)
    
    return '\n\n'.join(formatted_paragraphs)

st.title("Streaming 챗봇 (LaTeX 지원)")

# MathJax 설정
setup_latex_support()

# 메시지 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 이전 메시지들 표시
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(format_message(msg["content"]))

# 새로운 메시지가 있을 때 응답 생성
if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""
        
        # GPT에게 LaTeX 형식으로 수식을 출력하도록 지시
        messages = st.session_state["messages"].copy()
        messages.insert(0, {
            "role": "system",
            "content": "모든 수학 수식은 LaTeX 문법을 사용하여 작성해주세요. 인라인 수식은 $...$ 형식을, 별도 줄 수식은 $$...$$ 형식을 사용하세요."
        })
        
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True
        )
        
        for response in stream:
            if response.choices[0].delta.content is not None:
                content = response.choices[0].delta.content
                full_response += content
                # 실시간으로 LaTeX 렌더링
                response_container.markdown(format_message(full_response))
        
        st.session_state["messages"].append({"role": "assistant", "content": full_response})

# 채팅 입력 (페이지 하단에 위치)
st.markdown("<div style='padding: 3rem;'></div>", unsafe_allow_html=True)
user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.rerun()
