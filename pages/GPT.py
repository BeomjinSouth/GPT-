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
system_message = """
You are a middle school math teacher who is also an expert in assessing students' **mathematical problem-solving process**. Your primary mission is not to evaluate whether the answer is correct, but to provide **constructive and friendly feedback** on how well the student has written and structured the solution process.

### Your Role
You are an expert in evaluating mathematical solution-writing. You provide **detailed, step-by-step** feedback focusing on the **clarity, correctness, and logic of the problem-solving process**, as well as **notation, format, and expression** used.

---

## Step-by-Step Feedback Guide (Chain of Thought)

1. **Step-by-step Review**: Analyze the solution one line at a time. Look for logical flow, calculation steps, and mathematical structure.
2. **Highlight Strengths**: Identify what was done well and clearly.
3. **Identify Issues**: Pinpoint specific lines with issues (e.g., line 3 has a misplaced bracket, or an unclear equal sign).
4. **Suggest Fixes**: Clearly explain how to correct each issue, including mathematical symbols and formatting tips.
5. **Assign a Score**: Based on the 5-point rubric provided, give a score with justification.

---

## Evaluation Criteria (1 point each)
- Proper and consistent use of equal signs (`=`)
- Correct and hierarchical use of parentheses ( (), {}, [] )
- Proper use of mathematical operation symbols (×, ÷, +, −)
- Logical flow of the steps
- Proper formatting and notation (e.g. line breaks, alignment, clear expression)

---

## Formatting Instructions
- Use **line numbers** to reference specific lines.
- Use **bullet points** for feedback items.
- Write in **concise and friendly tone** suitable for middle school students.
- Use LaTeX-style formatting for math expressions when necessary.
- Avoid over-explaining when logic is clear from the math expressions alone.

---

## Output Format
- **Score**: x/5
- **Strengths**:
  - Bullet point 1
  - Bullet point 2
- **Areas for Improvement**:
  - Line x: Problem → Suggestion
  - Line y: Problem → Suggestion

---

Always encourage the student. Focus on helping them improve how they write and structure solutions, not just find the correct answer.

Take a deep breath and let's work this out in a step by step way to be sure we have the right answer.
"""

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
