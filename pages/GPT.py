import streamlit as st
import openai
import re

# LaTeX 수식 처리 함수
def process_latex(text):
    # '\times'나 'times'를 유니코드 곱셈 기호로 치환
    text = re.sub(r'\\times', '×', text)
    text = text.replace('times', '×')
    text = text.replace('**', '')
    
    # 수식 블록 처리
    def preserve_formula(match):
        formula = match.group(1)
        formula = ' '.join(formula.split())
        return f'${formula}$'
    
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: f'$${m.group(1).strip()}$$', text, flags=re.DOTALL)
    text = re.sub(r'\$(.*?)\$', preserve_formula, text)
    
    # 불필요한 공백 및 빈 줄 제거
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    processed_text = '\n'.join(lines)
    processed_text = re.sub(r'\n\s*\n', '\n\n', processed_text)
    return processed_text.strip()

st.title("루브릭 챗봇 - 성호중 범진")

# 세션 상태에 대화 메시지 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 이전 메시지들 표시
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown("**사용자:** " + process_latex(msg["content"]))
    else:
        st.markdown("**선생님:** " + process_latex(msg["content"]))

# 사용자 입력
user_input = st.text_input("선생님께 질문하세요...", key="input")
if st.button("전송") and user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    # 시스템 메시지와 기존 대화를 포함한 전체 메시지 구성
    messages = [{
        "role": "system",
        "content": (
            "당신은 중학교 학생들의 수행평가 분석적 채점기준표를 만들어주는 베테랑 교사입니다.\n\n"
            "루브릭은 평가 기준과 성과 수준에 대한 구체적인 서술로 구성되어야 하며, 단순히 과제 지시사항이나 체크리스트 형태가 되어서는 안 됩니다.\n"
            "평가 기준은 학습 결과(지식·기술 습득)를 반영해야 하고, 성과 수준 서술은 관찰 가능한 행동이나 결과를 구체적으로 설명해야 합니다.\n\n"
            "평가 기준 선정 시 유의사항:\n"
            "1. 학습 목표와의 일치\n"
            "2. 명확하고 관찰 가능함\n"
            "3. 서로 구별 가능하고 전체를 포괄함\n\n"
            "성과 수준 서술 작성 시 유의사항:\n"
            "1. 구체적이고 서술적인 기술\n"
            "2. 연속체의 명확성\n"
            "3. 평가 기준과 평행 구조\n\n"
            "루브릭은 단순한 점수 매기기를 넘어서 학생들의 학습 진행 상황을 진단하고 피드백하는 도구입니다."
        )
    }] + st.session_state["messages"]

    response_container = st.empty()
    full_response = ""
    
    # GPT API 호출 (스트리밍)
    with st.spinner("답변 생성 중..."):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True
        )
        for chunk in response:
            if "choices" in chunk and chunk["choices"][0].get("delta", {}).get("content"):
                delta = chunk["choices"][0]["delta"]["content"]
                full_response += delta
                response_container.markdown(process_latex(full_response))
    
    st.session_state["messages"].append({"role": "assistant", "content": full_response})
    st.experimental_rerun()
