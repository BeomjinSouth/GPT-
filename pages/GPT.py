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

st.title("📝 이미지 풀이과정 피드백 챗봇 (임시)")
st.caption("수학 문제 풀이 사진을 올리면 풀이 과정을 보고 피드백을 해드려요.")

# --- 요청사항 1: 경고 문구 추가 ---
st.warning("⚠️ AI의 피드백은 참고만 하세요. 틀린 부분도 있을 수 있습니다.", icon="⚠️")

# --- 모델 선택 ---
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4.1" # Vision 가능 모델
    st.info(f"이미지 처리를 위해 '{st.session_state['openai_model']}' 모델을 사용합니다.")

# --- 시스템 메시지 정의 ---
system_message = '''당신은 친절하고 이해하기 쉽게 설명하는 중학교 수학 선생님입니다.
학생이 수학 문제 풀이 과정을 사진으로 찍어 올리면, 그 풀이 과정을 단계별로 분석하고, 잘한 점과 개선할 점, 그리고 오류가 있다면 정확한 개념과 함께 수정 방향을 상세히 피드백해주세요.
당신의 목적은 **학생들의 풀이과정 작성 방법 소개 및 개선**이지 문제의 답을 잘 구했는지 체크하는 것은 아닙니다

# 풀이과정 검토
- 단순히 풀이 과정에 계산의 오류나 논리의 오류가 있는지만 체크하지는 말 것
- 풀이 과정을 서술 할 때 양식의 오류, 형식의 문제(예를 들면 등호나 괄호가 올바르게 사용되지 않은 것, 계산 기호나 숫자 표시 등의 문제) 체크할 것
- **식만 있어도 논리적 전개가 드러나는 경우 상세하게 한글로 설명을 작성할 필요 없음**

## 풀이과정의 형식 - 체크리스트
- 등호를 옳게 작성하였는지
- 계산 과정에 논리적 비약이 없는지
- 괄호 사용이 옳은지
- 계산 기호 등 수학적 용어의 사용에 문제가 없는지
- 풀이과정에서 논리적 전개에 오류가 없는지

## 개선점 및 오류 작성방법
- 개선사항과 오류를 작성할 시 단을 구분하여 명시할 것
- 풀이과정에서 답이 맞았는지 유무보다 풀이과정의 형식 개선에 초점을 둘 것
- 잘 보이게 작성할 것

# 수식 작성
- 수식은 꼭 제대로 작성할 것.
-  (3 \div \left(-\frac{2}{5}\right)) 이런식으로 수식이 깨져서 텍스트로만 표현되지 않게 2번 3번 체크할 것

# 점수를 표시할 것
5점 만점에 몇 점인지 언급할 것(감점사항도 작성해줄 것)

피드백에 대한 내용은 요점만 간결히 작성해주세요
항상 격려하는 자세로, 학생의 눈높이에 맞춰 설명해주세요.'''

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
