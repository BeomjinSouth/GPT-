import streamlit as st
from openai import OpenAI

# OpenAI API 키 설정
client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])

st.title("방학 수학 방과후 챗봇 - 성호중 박범진")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"
    
# ★ 시스템 메시지
system_message = """당신은 중학교 1학년에게 수학 문제의 해결 방법을 차근차근 안내하는 교사입니다. 
문제에 대해 곧바로 답을 알려주지 마세요. 당신은 문제를 대신 풀어주는 로봇이 아닙니다.
당신은 반드시 학생들이 풀이과정 중 오류가 있거나 이해가 안되는 부분이 있을 때 
해당하는 부분을 문답법을 통해 알려줘야 합니다.
챗봇을 활용하는 대상은 중학교 1학년 학생이기 때문에 한 번에 너무 많은 내용을 전달하지 않고 
조금씩 나눠서 전달합니다.
"""

# ★ 대화 내역 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ★ 시스템 메시지가 없다면 추가
if len(st.session_state["messages"]) == 0:
    st.session_state["messages"] = [{"role": "system", "content": system_message}]


# ★ 기존 메시지 출력
#   - Streamlit의 st.chat_message를 활용해서 role별로 채팅 형태 출력
for idx, msg in enumerate(st.session_state["messages"]):
    # 맨 처음 시스템 메시지는 굳이 사용자에게 직접 보여줄 필요 없으면 건너뛰어도 됨
    # if msg["role"] == "system": 
    #     continue
    if idx > 0:  # system 제외
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ★ 사용자 입력 (Streamlit 1.25 이상부터 st.chat_input 지원)
prompt = st.chat_input("안녕하세요? 수학 문제에 대해 저에게 알려주시고, 무엇이 궁금한지 여쭤보세요!")


# ★ 사용자 입력이 들어온 경우 처리
if prompt:
    # 1) 세션 스테이트에 사용자 메시지 추가
    st.session_state["messages"].append({"role": "user", "content": prompt})

    # 2) 사용자 메시지를 화면에 표시
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3) OpenAI ChatCompletion API 호출 (stream=True 설정)
    with st.chat_message("assistant"):
        response_container = st.empty()  # 스트리밍 출력용 플레이스홀더
        partial_response = ""

        # OpenAI ChatCompletion 호출
        completion_stream = client.chatcompletions.create(
            model=st.session_state["openai_model"],
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]],
            stream=True,
            temperature=0.7,
        )

        # 4) 스트리밍으로 chunk를 받아오면서 실시간으로 응답 표시
        for chunk in completion_stream:
            chunk_content = chunk["choices"][0]["delta"].get("content", "")
            partial_response += chunk_content
            # 채팅 메시지를 점진적으로 업데이트
            response_container.markdown(partial_response)

    # 5) 최종적으로 assistant 메시지에 전체 응답 저장
    st.session_state["messages"].append({"role": "assistant", "content": partial_response})
