import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from PIL import Image
import base64
import io

# .env 파일에서 환경 변수(OPENAI_API_KEY) 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI()


def encode_image_to_base64(image_file):
    """이미지 파일을 base64로 인코딩"""
    return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_all_images_with_vision(image_files_with_data):
    """
    GPT-4o Vision을 사용하여 모든 이미지를 일괄 분석
    중복 감지 기능 포함
    """
    try:
        # 프롬프트: 모든 이미지를 비교하며 분석
        analysis_prompt = """
당신은 스마트폰 사진첩 정리 전문가입니다.

업로드된 모든 사진을 분석하여 다음을 수행해주세요:

1. 각 사진을 다음 카테고리로 분류:
   - 영수증 캡처: 마트, 카페, 식당 등의 영수증 사진
   - 메모/문서: 손글씨 메모, 텍스트 위주의 문서, 화이트보드 사진
   - 중복 사진: 다른 사진과 내용이 거의 동일한 사진
   - 일반 사진: 풍경, 인물, 음식 등 보관할 가치가 있는 사진
   - 기타: 위의 카테고리에 해당하지 않는 사진

2. 중복 사진 감지:
   - 시각적으로 거의 동일하거나 매우 유사한 사진을 찾습니다
   - 중복 사진이 있다면, 원본으로 추정되는 사진 1장을 제외하고 나머지는 모두 "중복 사진"으로 분류합니다
   - 중복 사진에는 "이 사진은 [사진번호]와 중복입니다"라고 명시합니다

3. 각 사진별 응답 형식:
   [사진 번호]: [1번, 2번, 3번 등]
   [파일명]: [원본 파일명]
   [카테고리]: [분류 결과]
   [삭제 제안]: [예/아니오]
   [이유]: [구체적인 이유]

4. 마지막에 요약:
   [요약]: 총 [X]장 중 삭제 제안 [Y]장, 중복 사진 [Z]장

예시:
[사진 번호]: 1
[파일명]: photo1.jpg
[카테고리]: 일반 사진
[삭제 제안]: 아니오
[이유]: 풍경 사진으로 보관할 가치가 있습니다.

[사진 번호]: 2
[파일명]: photo2.jpg
[카테고리]: 중복 사진
[삭제 제안]: 예
[이유]: 이 사진은 사진 1번과 중복입니다. 원본 1장만 보관하고 나머지는 삭제를 권장합니다.
"""

        # 메시지 구성: 텍스트 + 모든 이미지
        message_content = [
            {
                "type": "text",
                "text": analysis_prompt
            }
        ]

        # 모든 이미지를 메시지에 추가
        for idx, (filename, image_data) in enumerate(image_files_with_data, 1):
            message_content.append({
                "type": "text",
                "text": f"[사진 {idx}: {filename}]"
            })
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}"
                }
            })

        # GPT-4o Vision API 호출 (모든 이미지 일괄 분석)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": message_content
                }
            ],
            max_tokens=2000
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"분석 오류: {str(e)}"


# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 사진첩 해결사", page_icon="📸", layout="wide")

st.title("📸 나만의 AI 해결사: 스마트폰 사진첩 정리 (v2.0)")
st.markdown("---")
st.write("사진을 업로드하면 AI가 자동으로 분석하여 삭제 여부를 제안해 드립니다.")
st.write("**영수증, 메모, 중복 사진 등을 자동으로 식별합니다. (중복 감지 기능 강화)**")

# 파일 업로더
st.subheader("📤 사진 업로드")
uploaded_files = st.file_uploader(
    "정리할 사진들을 선택해주세요 (JPG, PNG, JPEG):",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    help="여러 장의 사진을 한꺼번에 업로드할 수 있습니다. (중복 사진도 함께 올려주세요)"
)

if uploaded_files:
    st.markdown("---")

    # 업로드된 이미지 미리보기
    st.subheader(f"📋 업로드된 사진 ({len(uploaded_files)}장)")

    # 썸네일 표시
    cols = st.columns(min(len(uploaded_files), 5))
    for idx, uploaded_file in enumerate(uploaded_files):
        with cols[idx % 5]:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"사진 {idx + 1}", use_column_width=True)

    st.markdown("---")

    # 분석 버튼
    if st.button("🔍 전체 분석 시작 (중복 감지 포함)", use_container_width=True):
        with st.spinner("AI가 모든 사진을 분석 중입니다... (중복 감지 포함)"):
            # 모든 이미지 인코딩
            image_files_with_data = []
            for uploaded_file in uploaded_files:
                uploaded_file.seek(0)
                image_data = encode_image_to_base64(uploaded_file)
                image_files_with_data.append((uploaded_file.name, image_data))

            # 일괄 분석
            analysis_result = analyze_all_images_with_vision(image_files_with_data)

            # 결과 표시
            st.markdown("---")
            st.subheader("📊 분석 결과 (일괄 분석)")
            st.markdown(analysis_result)

            # 결과 다운로드
            st.download_button(
                label="📥 분석 결과 다운로드 (텍스트)",
                data=analysis_result,
                file_name="photo_analysis_result.txt",
                mime="text/plain"
            )

else:
    st.info("💡 사진을 업로드하면 AI가 자동으로 분석을 시작합니다. 중복 사진도 함께 올려주세요!")

# 하단 정보
st.markdown("---")
st.info("""
**v2.0 업그레이드 사항:**
- ✅ **중복 감지 강화**: 모든 사진을 일괄 분석하여 중복 사진을 정확히 감지합니다.
- ✅ **명시적 중복 표시**: 중복 사진에는 "이 사진은 [사진번호]와 중복입니다"라고 명확히 표시됩니다.
- ✅ **일괄 분석**: 사진을 한 장씩 분석하지 않고 모두 함께 비교하여 분석합니다.
- ✅ **결과 다운로드**: 분석 결과를 텍스트 파일로 다운로드할 수 있습니다.

**사용 방법:**
1. 정리하고 싶은 사진들을 모두 업로드합니다 (중복 사진도 함께).
2. "전체 분석 시작" 버튼을 클릭합니다.
3. AI가 모든 사진을 비교하며 분석하여 결과를 표시합니다.
4. 필요시 결과를 다운로드합니다.

**주의사항:**
- 텍스트 기반 분석이므로 100% 정확하지 않을 수 있습니다.
- 최종 삭제 여부는 사용자의 판단으로 결정해주세요.
""")