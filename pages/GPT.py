import streamlit as st
from openai import OpenAI

# OpenAI API 키 설정
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

st.title("임시용 챗봇 - 성호중 박범진")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "o3-mini-2025-01-31"

system_message = '''All messages are so important. Take step by step. If you want more information, get it before answer.
당신은 중학교 학생들의 수행평가 분석적 채점기준표를 만들어주는 베테랑 교사입니다. 

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

 
'''

if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    st.session_state.messages = [{"role": "system", "content": system_message}]

for idx, message in enumerate(st.session_state.messages):
    if idx > 0:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("안녕하세요?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
