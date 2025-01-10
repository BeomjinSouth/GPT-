import streamlit as st
from openai import OpenAI
import re

# OpenAI 객체 생성
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])
def process_latex(text):
    """LaTeX 수식과 텍스트 처리를 위한 함수"""
    
    # 1. times 표기를 먼저 처리
    text = text.replace('times', '\\times')
    
    # 2. 괄호 및 수식 보존
    def preserve_formula(match):
        formula = match.group(1).strip()
        # 수식 내부 정리 (불필요한 공백 제거 및 기호 정리)
        formula = re.sub(r'\s+', ' ', formula)
        return f'${formula}$'

    # 3. 수식 처리 ($$...$$와 $...$)
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: f'$${m.group(1).strip()}$$', text, flags=re.DOTALL)
    text = re.sub(r'\$([^$]+)\$', preserve_formula, text)
    
    # 4. 텍스트 줄바꿈 처리
    # 문장 단위로 분리하여 처리
    sentences = []
    for line in text.split('\n'):
        if line.strip():
            # 문장 끝 표시가 있는 경우 줄바꿈 추가
            parts = re.split(r'([.!?][\s]*)', line)
            for i in range(0, len(parts)-1, 2):
                sentence = parts[i] + parts[i+1]
                sentences.append(sentence.strip())
            if len(parts) % 2 == 1 and parts[-1].strip():
                sentences.append(parts[-1].strip())
    
    # 5. 최종 텍스트 조합
    result = '\n\n'.join(sentences)
    
    # 6. 연속된 공백 제거
    result = re.sub(r'\n\s*\n', '\n\n', result)
    
    return result

# 스타일 부분도 수정
st.markdown("""
    <style>
        .katex { font-size: 1.1em; }
        .katex-display { 
            overflow: visible;
            margin: 1em 0;
        }
        .element-container {
            margin-bottom: 1em;
        }
        .markdown-text-container {
            line-height: 1.8;
        }
        /* 줄바꿈 강제 방지 */
        .katex-html {
            white-space: nowrap !important;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("중1 수학 선생님 챗봇-성호중 범진")

# 메시지 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# KaTeX 스타일 추가
st.markdown("""
    <style>
        .katex { font-size: 1.1em; }
        .katex-display { 
            overflow: auto hidden;
            white-space: nowrap;
        }
        .element-container {
            overflow-x: auto;
        }
        .markdown-text-container {
            line-height: 1.6;
        }
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
            챗봇을 활용하는 대상은 중학교 1학년 학생이기 때문에 한 번에 6문장을 넘게 전달하지 않고 차근차근 내용을 전달합니다. 
            중간중간 이해가 잘 되고 있는지 지속적으로 체크하세요.
            
            수식 작성 시 다음 규칙을 반드시 지켜주세요:
            1. 음수의 제곱은 반드시 괄호로 감싸주세요. 예: $(-1)^2$
            2. 곱셈은 반드시 \\times를 사용하세요
            3. 인라인 수식은 $...$ 로 표시하세요
            4. 디스플레이 수식은 $$...$$로 표시하세요
            5. 수식 안에서 설명이나 강조를 위한 ** 사용을 피하세요"""
        })
        
        stream = client.chat.completions.create(
            model="chatgpt-4o-latest",  # 요청하신 모델로 변경
            messages=messages,
            stream=True
        )
        
        for response in stream:
            if response.choices[0].delta.content is not None:
                content = response.choices[0].delta.content
                full_response += content
                response_container.markdown(process_latex(full_response))
        
        st.session_state["messages"].append({"role": "assistant", "content": full_response})

# 채팅 입력
st.markdown("<div style='padding: 3rem;'></div>", unsafe_allow_html=True)
user_input = st.chat_input("선생님께 질문하세요...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.rerun()
