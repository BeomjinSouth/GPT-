import streamlit as st
from openai import OpenAI
import re

# OpenAI 객체 생성
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

def process_latex(text):
    """LaTeX 수식을 Streamlit markdown 형식으로 변환"""
    # [수식] 형태를 $$수식$$ 형태로 변환
    text = re.sub(r'\[(.*?)\]', r'$$\1$$', text, flags=re.DOTALL)
    
    # 불릿 포인트 및 줄바꿈 보존
    lines = []
    for line in text.split('\n'):
        if line.strip().startswith('*'):
            # 불릿 포인트 라인은 그대로 유지
            lines.append(line)
        else:
            lines.append(line)
    
    return '\n\n'.join(lines)

st.title("Streaming 챗봇 (LaTeX 지원)")

# 메시지 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 스타일 추가
st.markdown("""
    <style>
        .katex { font-size: 1.1em; }
        .element-container { margin-bottom: 0.5em; }
    </style>
    """, unsafe_allow_html=True)

# 메시지 컨테이너 생성
message_container = st.container()

# 이전 메시지들 표시
with message_container:
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(process_latex(msg["content"]))

# 새로운 메시지가 있을 때 응답 생성
if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""
        
        # GPT에게 LaTeX 형식으로 수식을 출력하도록 지시
        messages = st.session_state["messages"].copy()
        messages.insert(0, {
            "role": "system",
            "content": "수학 수식을 작성할 때는 다음 규칙을 따르세요:\n"
                      "1. 인라인 수식은 $$...$$로 감싸주세요\n"
                      "2. 별도 줄 수식도 $$...$$로 감싸주세요\n"
                      "3. LaTeX 문법을 사용하여 수식을 작성해주세요"
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
                response_container.markdown(process_latex(full_response))
        
        st.session_state["messages"].append({"role": "assistant", "content": full_response})

# 채팅 입력 (페이지 하단에 위치)
st.markdown("<div style='padding: 3rem;'></div>", unsafe_allow_html=True)
user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.rerun()
