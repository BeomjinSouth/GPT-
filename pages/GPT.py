import streamlit as st
from openai import OpenAI
import re

# OpenAI 객체 생성
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

def process_latex(text):
    """LaTeX 수식을 처리하고 줄바꿈을 HTML <br> 태그로 치환하는 함수"""
    
    # '\\times'나 'times' 모두 유니코드 곱셈 기호 '×'로 치환
    text = re.sub(r'\\times', '×', text)
    text = text.replace('times', '×')
    text = text.replace('**', '')
    
    # 수식 블록 처리 함수
    def preserve_formula(match):
        formula = match.group(1)
        formula = ' '.join(formula.split())
        return f'${formula}$'
    
    # 수식 패턴 ($...$ 또는 $$...$$) 찾아서 처리
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: f'$${m.group(1).strip()}$$', text, flags=re.DOTALL)
    text = re.sub(r'\$(.*?)\$', preserve_formula, text)
    
    # 줄바꿈 처리: 각 줄의 앞뒤 공백 제거 후 줄이 있으면 리스트에 추가
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line:
            # 번호로 시작하는 줄은 앞뒤로 빈 줄 추가
            if re.match(r'^\d+\.', line):
                lines.extend(['', line, ''])
            else:
                lines.append(line)
    text = '\n'.join(lines)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 최종적으로 모든 줄바꿈을 <br> 태그로 변환
    text = text.strip().replace("\n", "<br>")
    return text

st.title("루브릭 챗봇-성호중 범진")

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

# 메시지 컨테이너 생성 및 이전 메시지들 표시
message_container = st.container()
with message_container:
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(process_latex(msg["content"]), unsafe_allow_html=True)

# 새로운 메시지가 있을 때 응답 생성
if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""
        
        messages = st.session_state["messages"].copy()
        messages.insert(0, {
            "role": "system",
            "content": (
                "당신은 중학교 학생들의 수행평가 분석적 채점기준표를 만들어주는 베테랑 교사입니다. \n"
                "채점기준표를 작성할 때의 규칙은 다음과 같습니다\n"
                "# 루브릭의 기본 구성\n\n"
                "루브릭은 평가 기준과 성과 수준에 대한 구체적인 서술로 구성되어야 하며, 단순히 과제 지시사항이나 체크리스트 형태가 되어서는 안 됩니다.\n"
                "평가 기준은 학습 결과(지식·기술 습득)를 반영해야 하고, 성과 수준 서술은 관찰 가능한 행동이나 결과를 구체적으로 설명해야 합니다.\n\n"
                "## 평가 기준 선정 시 유의사항\n"
                "1. 학습 목표와의 일치: 평가 기준은 과제 자체의 요구사항(예, 포스터의 구성요소)이 아니라, 그 과제를 통해 학생
