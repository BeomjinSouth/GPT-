import streamlit as st
from openai import OpenAI
import re

# OpenAI 객체 생성
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

def process_latex(text):
    """모든 수식을 LaTeX 형식으로 변환"""
    
    # 1. 특수 패턴 치환
    replacements = {
        '-{1}^{2}': '(-1)^{2}',
        '\\$\\$\\$': '$$',
        '\\*\\*': '',  # ** 제거
        '{1}$^{2}': '{1}^{2}',
        '\\${1}': '$1',
        '\\${2}': '$2',
        'S{1}': '-1',
        'S{2}': '-1',
        'times S': '\\times (-)',
        '**−1**': '$-1$',
        '**1**': '$1$'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # 2. 중괄호 안의 수식 처리
    text = re.sub(r'\{(\d+)\}', r'{\1}', text)
    
    # 3. LaTeX 수식 블록 정리
    text = re.sub(r'\${2,}(.*?)\${2,}', r'$$\1$$', text, flags=re.DOTALL)
    
    # 4. 인라인 수식 처리
    lines = []
    for line in text.split('\n'):
        count = line.count('$')
        if count % 2 == 1:
            if line.count('$$') == 0:
                line += '$'
        lines.append(line)
    text = '\n'.join(lines)
    
    # 5. 최종 정리
    text = text.replace('\\neq', '\\neq ')
    text = text.replace('××', '\\times')
    
    return text

st.title("중1 수학 선생님 챗봇-성호중 범진")

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
        
        messages = st.session_state["messages"].copy()
        messages.insert(0, {
            "role": "system",
            "content": """당신은 중학교 1학년에게 수학 문제의 해결 방법을 차근차근 안내하는 교사입니다. 
            문제에 대해 곧바로 답을 알려주지 마세요. 당신은 문제를 대신 풀어주는 로봇이 아닙니다. 
            당신은 반드시 학생들이 풀이과정 중 오류가 있거나 이해가 안되는 부분이 있을 때 해당하는 부분을 문답법을 통해 알려줘야합니다. 
            챗봇을 활용하는 대상은 중학교 1학년 학생이기 때문에 한 번에 6문장을 넘게 전달하지 않고 차근차근 내용을 전달합니다. 중간중간 이해가 잘 되고 있는지 지속적으로 체크하세요"""
        })
        
        stream = client.chat.completions.create(
            model="chatgpt-4o-latest",
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
user_input = st.chat_input("선생님께 질문하세요...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.rerun()
