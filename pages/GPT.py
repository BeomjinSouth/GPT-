import streamlit as st
from openai import OpenAI
import re

# OpenAI 객체 생성
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])
def process_latex(text):
    """모든 수식을 LaTeX 형식으로 변환"""
    # 1. 중복된 기호 정리
    text = text.replace('××', '\\times')
    text = text.replace('$$$$', '$$')
    
    # 2. 잘못된 수식 형식 수정
    text = text.replace('-1$ \\times $-1', '$-1 \\times -1$')
    text = text.replace('−12−12', '$(-1)^2$')
    
    # 3. 수식 블록 처리
    # 여러 줄 수식 처리
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: f'$${m.group(1).strip()}$$', text, flags=re.DOTALL)
    
    # 4. 인라인 수식 처리
    # 괄호로 둘러싸인 수식 표현을 $...$ 로 변환
    text = re.sub(r'\(([^$].*?)\)', 
                 lambda m: '$' + m.group(1) + '$' 
                 if any(c in m.group(1) for c in ['^', '\\', '+', '=', '-', '±', '≠', '×']) 
                 else '(' + m.group(1) + ')', text)
    
    # 5. LaTeX 특수 문자 처리
    text = text.replace('\\neq', '\\neq ')
    text = re.sub(r'(?<!{)(\d+)(?!})', r'{\1}', text)  # 숫자를 중괄호로 감싸기
    
    # 6. 줄바꿈 처리
    lines = [line for line in text.split('\n') if line.strip()]
    
    return '\n\n'.join(lines)

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
            챗봇을 활용하는 대상은 중학교 1학년 학생이기 때문에 한 번에 너무 많은 내용을 전달하지 않고 약간의 정보량으로 조금씩 나눠서 전달합니다.
            수식 작성 시 다음 규칙을 엄격히 따라주세요:
            1. 인라인 수식은 반드시 하나의 $...$ 로 감싸주세요 (중복 사용 금지)
            2. 별도 줄 수식은 하나의 $$...$$ 로 감싸주세요
            3. 곱셈 기호는 반드시 \\times 를 사용해주세요
            4. 지수는 반드시 ^{지수} 형태로 작성해주세요 (예: $2^{2}$)
            5. 음수의 제곱은 반드시 괄호로 감싸주세요 (예: $(-1)^{2}$)
            6. 수식 내 숫자는 모두 중괄호로 감싸주세요 (예: ${2} \\times {2}$)
            7. 수식 기호를 중복해서 사용하지 마세요"""
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
