import streamlit as st
from openai import OpenAI
import base64 # 이미지 인코딩을 위해 추가
from PIL import Image # 이미지 처리를 위해 추가
import io # 이미지 바이트 처리를 위해 추가

# --- OpenAI API 키 설정 ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"OpenAI API 키를 로드하는 중 오류 발생: {e}")
    st.error("st.secrets에 OpenAI API 키가 올바르게 설정되었는지 확인하세요.")
    st.stop() # 키가 없으면 앱 실행 중지

st.title("📝 이미지 풀이과정 피드백 챗봇 (임시) - 범진쌤")
st.caption("수학 문제 풀이 사진을 올리면 풀이 과정을 보고 피드백을 해드려요.")

# --- 요청사항 1: 경고 문구 추가 ---
st.warning("⚠️ AI의 피드백은 참고만 하세요. 틀린 부분도 있을 수 있습니다.", icon="⚠️")

# --- 모델 선택 ---
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4.1" # Vision 가능 모델
    st.info(f"이미지 처리를 위해 '{st.session_state['openai_model']}' 모델을 사용합니다.")

# --- 시스템 메시지 정의 ---
system_message =  ''''당신은 친절하고 이해하기 쉽게 설명하는 중학교 수학 선생님입니다.
학생이 수학 문제 풀이 과정을 사진으로 찍어 올리면, 그 풀이 과정을 단계별로 분석하고, 잘한 점과 개선할 점, 그리고 오류가 있다면 정확한 개념과 함께 수정 방향을 상세히 피드백해주세요.
당신의 목적은 **학생들의 풀이과정 작성 방법 소개 및 개선**이지 문제의 답을 잘 구했는지 체크하는 것은 아닙니다

학생이 풀이 과정을 사진으로 올리면 다음 세 가지 관점으로 간결하고 격려하는 어조로 피드백합니다.  

1️. **잘한 점**  
- 풀이과정에서 잘 작성한 부분을 간략하게 언급

2️. **개선할 점**  
    - 형식: 등호·괄호·기호 사용, 식 표기 오류  
    - 논리: 단계 간 비약이나 생략된 설명
        - 단 간단한 나눗셈, 곱셈, 덧셈, 뺄셈, 거듭제곱 정도는 별개로 언급하지 않고 바로 풀이과정을 작성해도 됨
    - 수식: LaTeX·텍스트가 깨지지 않도록 정확히 재작성  
        -  (3 \div \left(-\frac{2}{5}\right)) 이런식으로 수식이 깨져서 텍스트로만 표현되지 않게 2번 3번 체크할 것
    - 괄호 사용이 옳은지(대괄호, 중괄호, 소괄호)
        - 소괄호만 연속으로 사용하면 안됨
        - 괄호의 위계가 정확히 사용되어있는지 체크할 것(소괄호, 중괄호, 대괄호)
            - 위계가 정확하지 않다면 몇번째 줄의 어떤 괄호가 정확하게 쓰이지 않았는지, 어떻게 수정되어야하는지 언급할 것
        - 덧셈, 뺄셈, 곱셈, 나눗셈 기호가 연속으로 괄호 구분 없이 쓰인 것이 있는지
    - 풀이과정은 **식만으로 이뤄져도 무방함.** 별도의 설명을 작성할 필요 없음.
    

3️. **오류 수정 방향**  
   - 개념이 잘못된 부분은 정확한 정의와 예시로 간단히 안내  
   - 몇 번째 줄의 어느 부분을 어떻게 고쳐야 하는지 구체 제시  
   
4. **채점에 고려하지 않아도 되는 것**
- 곱셈 나눗셈은 덧셈 뺄셈보다 우선하기 때문에, 이것을 중괄호로 굳이 구분해서 작성할 필요 없음
- 간단한 나눗셈, 곱셈, 덧셈, 뺄셈 정도는 별개로 언급하지 않고 바로 풀이과정을 작성해도 됨
- 풀이과정은 식만으로 이뤄져도 무방함. 별도의 설명을 작성할 필요 없음


마지막에 **5점 만점 채점** 결과와 감점 사유를 요약합니다.  
답 자체보다는 ‘풀이 과정을 명료하게 쓰는 방법’을 안내하는 데 집중하세요.  
항상 학생의 눈높이에 맞춰, 짧고 친절하게 작성해 주세요.'''

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_message}]

# --- 챗봇 새로고침 버튼 ---
if st.button("🔄️ 대화 초기화"):
    st.session_state.messages = [{"role": "system", "content": system_message}]
    st.rerun() # 페이지 새로고침하여 채팅 로그 지우기

# --- 이전 대화 기록 표시 ---
for idx, message in enumerate(st.session_state.messages):
    if idx > 0:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], str):
                st.markdown(message["content"])
            elif isinstance(message["content"], list):
                for item in message["content"]:
                    if item["type"] == "text":
                        st.markdown(item["text"])

# --- 이미지 업로드 기능 ---
uploaded_file = st.file_uploader("풀이 과정 사진을 올려주세요 (JPG, PNG)", type=["jpg", "png"])

# --- 이미지 처리 및 피드백 요청 ---
if uploaded_file is not None:
    # 1. 이미지 표시
    image = Image.open(uploaded_file)
    # --- 요청사항 2: use_column_width -> use_container_width 변경 ---
    st.image(image, caption="첨부된 풀이 과정 이미지", use_container_width=True) # 수정된 부분

    # 2. 이미지를 base64로 인코딩
    buffered = io.BytesIO()
    image_format = image.format if image.format in ["JPEG", "PNG"] else "PNG"
    image.save(buffered, format=image_format)
    img_byte = buffered.getvalue()
    img_base64 = base64.b64encode(img_byte).decode('utf-8')

    # 3. 사용자 메시지 (이미지 포함) 구성
    user_message_content = [
        {"type": "text", "text": "이 이미지에 있는 수학 풀이 과정을 보고 피드백 해주세요."},
        {"type": "image_url", "image_url": {"url": f"data:image/{image_format.lower()};base64,{img_base64}"}}
    ]

    # 4. 세션 상태에 사용자 메시지 추가 (표시용)
    st.session_state.messages.append({"role": "user", "content": f"이미지 분석 요청: {uploaded_file.name}"})

    # 5. 실제 API 전송용 메시지 준비
    messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
    messages_for_api.append({"role": "user", "content": user_message_content})

    # 6. OpenAI API 호출 (Vision 모델 사용)
    try:
        with st.chat_message("assistant"):
            with st.spinner("이미지를 분석하고 피드백을 생성하는 중..."):
                response = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=messages_for_api,
                    max_completion_tokens=1024
                )
                full_response = response.choices[0].message.content
                st.markdown(full_response)

        # 7. 세션 상태에 어시스턴트 응답 추가
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"OpenAI API 호출 중 오류 발생: {e}")
        if st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()

# --- 텍스트 기반 챗봇 입력 ---
if prompt := st.chat_input("질문이 있나요? (텍스트로 질문)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    try:
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하는 중..."):
                response = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=messages_for_api,
                    max_completion_tokens=500
                )
                full_response = response.choices[0].message.content
                st.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"OpenAI API 호출 중 오류 발생: {e}")
        if st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()
