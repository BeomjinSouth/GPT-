import streamlit as st
from openai import OpenAI
import base64 # 이미지 인코딩을 위해 추가
from PIL import Image # 이미지 처리를 위해 추가
import io # 이미지 바이트 처리를 위해 추가

# --- OpenAI API 키 설정 ---
# Streamlit Community Cloud에 배포하는 경우 st.secrets 사용이 좋습니다.
# 로컬에서 테스트하는 경우, 환경 변수나 직접 키를 입력할 수 있습니다. (보안 주의)
try:
    client = OpenAI(api_key=st.secrets["OPENAI"]["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"OpenAI API 키를 로드하는 중 오류 발생: {e}")
    st.error("st.secrets에 OpenAI API 키가 올바르게 설정되었는지 확인하세요.")
    st.stop() # 키가 없으면 앱 실행 중지

st.title("📝 이미지 풀이과정 피드백 챗봇 (임시)")
st.caption("수학 문제 풀이 사진을 올리면 풀이 과정을 보고 피드백을 해드려요.")

# --- 모델 선택 ---
# 이미지 처리를 위해서는 Vision 기능이 있는 모델이 필요합니다.
# gpt-4o 또는 gpt-4-turbo와 같은 최신 모델을 사용하는 것이 좋습니다.
# o3-mini 모델은 이미지 처리를 지원하지 않습니다.
# 중요: Vision 모델은 기존 텍스트 모델보다 비용이 더 많이 발생할 수 있습니다.
if "openai_model" not in st.session_state:
    # st.session_state["openai_model"] = "o3-mini-2025-01-31" # 기존 모델 (이미지 처리 불가)
    st.session_state["openai_model"] = "gpt-4o" # Vision 가능 모델로 변경 (최신 모델 확인 필요)
    st.info(f"이미지 처리를 위해 '{st.session_state['openai_model']}' 모델을 사용합니다.")

# --- 시스템 메시지 정의 ---
system_message = '''당신은 친절하고 이해하기 쉽게 설명하는 중학교 수학 선생님입니다.
학생이 수학 문제 풀이 과정을 사진으로 찍어 올리면, 그 풀이 과정을 단계별로 분석하고, 잘한 점과 개선할 점, 그리고 오류가 있다면 정확한 개념과 함께 수정 방향을 상세히 피드백해주세요.
당신의 목적은 **학생들의 풀이과정 작성 방법 소개 및 개선**이지 문제의 답을 잘 구했는지 체크하는 것은 아닙니다

# 풀이과정 검토
- 단순히 풀이 과정에 계산의 오류나 논리의 오류가 있는지만 체크하지 않음
- 논술형으로 풀이 과정을 서술 할 때 양식의 오류, 형식의 문제 체크할 것

## 풀이과정의 형식 - 체크리스트
- 등호를 옳게 작성하였는지
- 계산 과정에 논리적 비약이 없는지
- 괄호 사용이 옳은지
- 계산 기호 등 수학적 용어의 사용에 문제가 없는지
- 풀이과정에서 논리적 전개가 들어가는지

## 개선점 및 오류 작성방법
- 개선사항과 오류를 작성할 시 단을 구분하여 명시할 것
- 풀이과정에서 답이 맞았는지 유무보다 풀이과정의 형식 개선에 초점을 둘 것
- 잘 보이게 작성할 것

항상 격려하는 말투를 사용하고, 학생의 눈높이에 맞춰 설명해주세요.'''

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_message}]

# --- 챗봇 새로고침 버튼 ---
if st.button("🔄️ 대화 초기화"):
    st.session_state.messages = [{"role": "system", "content": system_message}]
    st.rerun() # 페이지 새로고침하여 채팅 로그 지우기

# --- 이전 대화 기록 표시 ---
# 시스템 메시지는 제외하고 표시 (idx > 0 조건)
for idx, message in enumerate(st.session_state.messages):
    if idx > 0:
        with st.chat_message(message["role"]):
            # 이미지 데이터가 content에 포함된 경우 (base64 문자열 등)는 직접 표시하지 않음
            if isinstance(message["content"], str):
                st.markdown(message["content"])
            elif isinstance(message["content"], list): # Vision API 요청 형식 처리
                for item in message["content"]:
                    if item["type"] == "text":
                        st.markdown(item["text"])
                    # 이미지는 업로드 시점에 별도로 표시하므로 여기서는 텍스트만 표시
                    # 필요하다면 이미지 표시 로직 추가 가능

# --- 이미지 업로드 기능 ---
uploaded_file = st.file_uploader("풀이 과정 사진을 올려주세요 (JPG, PNG)", type=["jpg", "png"])

# --- 이미지 처리 및 피드백 요청 ---
if uploaded_file is not None:
    # 1. 이미지 표시
    image = Image.open(uploaded_file)
    st.image(image, caption="첨부된 풀이 과정 이미지", use_column_width=True)

    # 2. 이미지를 base64로 인코딩
    buffered = io.BytesIO()
    # 이미지 형식 확인 및 저장 (PNG 권장)
    image_format = image.format if image.format in ["JPEG", "PNG"] else "PNG"
    image.save(buffered, format=image_format)
    img_byte = buffered.getvalue()
    img_base64 = base64.b64encode(img_byte).decode('utf-8')

    # 3. 사용자 메시지 (이미지 포함) 구성
    user_message_content = [
        {
            "type": "text",
            "text": "이 이미지에 있는 수학 풀이 과정을 보고 피드백 해주세요."
        },
        {
            "type": "image_url",
            "image_url": {
                # f"data:image/{image_format.lower()};base64,{img_base64}"
                # 위 형식 대신 아래처럼 분리해도 최신 API에서 잘 동작하는 경우가 많습니다.
                "url": f"data:image/{image_format.lower()};base64,{img_base64}"
            }
        }
    ]

    # 4. 세션 상태에 사용자 메시지 추가 (표시용 텍스트와 실제 전송 내용 분리 가능)
    # 표시용 메시지 (간단하게)
    st.session_state.messages.append({"role": "user", "content": f"이미지 분석 요청: {uploaded_file.name}"})
    # 실제 API 전송용 메시지 준비 (이전 대화 포함)
    messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]] # 방금 추가한 표시용 메시지는 제외
    messages_for_api.append({"role": "user", "content": user_message_content}) # 실제 이미지 포함 메시지 추가

    # 5. OpenAI API 호출 (Vision 모델 사용)
    try:
        with st.chat_message("assistant"):
            with st.spinner("이미지를 분석하고 피드백을 생성하는 중..."):
                response = client.chat.completions.create(
                    model=st.session_state["openai_model"], # Vision 가능 모델 사용
                    messages=messages_for_api,
                    # max_tokens=1024 # 이 부분을 수정
                    max_completion_tokens=1024 # 이렇게 수정
                )
                full_response = response.choices[0].message.content
                st.markdown(full_response)


        # 6. 세션 상태에 어시스턴트 응답 추가
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"OpenAI API 호출 중 오류 발생: {e}")
        # 실패 시 추가된 사용자 메시지(표시용) 제거 가능
        if st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()

    # 처리 후 업로드 상태 초기화 (선택 사항, 다시 올릴 수 있게)
    # st.rerun() # 또는 uploaded_file = None 등으로 초기화

# --- 텍스트 기반 챗봇 입력 ---
if prompt := st.chat_input("질문이 있나요? (텍스트로 질문)"):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # API 요청 메시지 준비 (텍스트만 포함)
    messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    # OpenAI API 호출 (텍스트 처리)
    try:
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하는 중..."):
                response = client.chat.completions.create(
                    model=st.session_state["openai_model"], # 동일 모델 사용 (Vision 모델도 텍스트 처리 가능)
                    messages=messages_for_api,
                    # max_tokens=500 # 이 부분을 수정
                    max_completion_tokens=500 # 이렇게 수정
                )
                full_response = response.choices[0].message.content
                st.markdown(full_response)

        # 세션 상태에 어시스턴트 응답 추가
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"OpenAI API 호출 중 오류 발생: {e}")
        # 실패 시 추가된 사용자 메시지 제거 가능
        if st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()
