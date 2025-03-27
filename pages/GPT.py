import streamlit as st
from openai import OpenAI
import re

# OpenAI 객체 생성
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])
def process_latex(text):
    """LaTeX 수식을 처리하는 함수"""
    
    # '\\times'나 'times' 모두 유니코드 곱셈 기호 '×'로 치환
    text = re.sub(r'\\times', '×', text)
    text = text.replace('times', '×')
    text = text.replace('**', '')

    # 수식 블록 처리
    def preserve_formula(match):
        """수식 블록 내용을 보존하고 정리"""
        formula = match.group(1)
        # 수식 내부 공백 정리
        formula = ' '.join(formula.split())
        return f'${formula}$'
    
    # 수식 패턴 ($...$ 또는 $$...$$) 찾아서 처리
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: f'$${m.group(1).strip()}$$', text, flags=re.DOTALL)
    text = re.sub(r'\$(.*?)\$', preserve_formula, text)
    
    # 줄바꿈 처리
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line:
            # 번호로 시작하는 줄은 앞뒤로 빈 줄 추가
            if re.match(r'^\d+\.', line):
                lines.extend(['', line, ''])
            else:
                lines.append(line)
    
    # 연속된 빈 줄 제거
    text = '\n'.join(lines)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()



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
            "content": """당신은 중학교 학생들의 수행평가 분석적 채점기준표를 만들어주는 베테랑 교사입니다. 
            채점기준표를 작성할 때의 규칙은 다음과 같습니다
            # 루브릭의 기본 구성
            
            루브릭은 평가 기준과 성과 수준에 대한 구체적인 서술로 구성되어야 하며, 단순히 과제 지시사항이나 체크리스트 형태가 되어서는 안 됩니다.
            평가 기준은 학습 결과(지식·기술 습득)를 반영해야 하고, 성과 수준 서술은 관찰 가능한 행동이나 결과를 구체적으로 설명해야 합니다.
            ​
            ## 평가 기준 선정 시 유의사항
            1. 학습 목표와의 일치: 평가 기준은 과제 자체의 요구사항(예, 포스터의 구성요소)이 아니라, 그 과제를 통해 학생이 달성해야 할 학습 결과와 연결되어야 합니다            
            2. 명확하고 관찰 가능함: 기준은 학생과 교사가 모두 이해할 수 있도록 명확하게 정의되어야 하며, 실제 학생 작업에서 관찰할 수 있어야 합니다.
            3. 서로 구별 가능하고 전체를 포괄함: 각 기준은 서로 중복되지 않으면서도, 전체 학습 목표를 완전히 반영할 수 있도록 구성해야 합니다.
            ​
            
            ## 성과 수준 서술 작성 시 유의사항
            구체적이고 서술적인 기술: 단순히 “우수, 보통, 미흡” 같은 평가 등급 대신, 각 수준에서 학생의 작업이 실제로 어떻게 나타나는지를 구체적으로 서술해야 합니다.
            연속체의 명확성: 하위 수준부터 상위 수준까지 명확하게 구분될 수 있도록, 각 단계 간 차이점을 분명히 해야 합니다.
            평가 기준과 평행 구조: 각 성과 수준의 서술은 동일한 평가 기준의 같은 측면을 다루어야 하며, 학생들이 자신의 강점과 개선점을 명확히 인식할 수 있도록 해야 합니다.
            ​
            ## 루브릭의 용도 및 활용
            학습 도구로서의 역할: 루브릭은 단순히 점수를 매기는 도구가 아니라, 학생들이 자신의 학습 목표를 이해하고 자가 평가 및 피드백을 받을 수 있도록 돕는 도구입니다.
            학생과의 공유: 루브릭은 과제 시작 전 학생과 공유되어야 하며, 이를 통해 학생들이 작업 전반에서 무엇을 중점적으로 개선해야 하는지 명확히 인식할 수 있습니다.

            ## 기타 루브릭에 대한 안내
            효과적인 루브릭 작성은 '학습 결과'에 초점을 맞추어 평가 기준을 명확하고 관찰 가능하게 정의하고, 각 기준에 대해 구체적이며 구분이 명확한 서술적 성과 수준을 제시하는 것에 있습니다. 이를 통해 루브릭은 단순한 점수 매기기를 넘어서, 학생들의 학습 진행 상황을 진단하고 피드백하는 강력한 학습 도구로 활용될 수 있습니다
            """
        })
        
        stream = client.chat.completions.create(
            model="o3-mini-2025-01-31",  # 요청하신 모델로 변경
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
