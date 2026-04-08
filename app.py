import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from PIL import Image
import base64

# .env 파일에서 환경 변수 로드
load_dotenv()

# API 키 확인
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY가 설정되지 않았습니다!")
    st.stop()

# OpenAI 클라이언트 초기화 (proxies 파라미터 없음)
client = OpenAI(api_key=api_key)


def encode_image_to_base64(image_file):
    """이미지 파일을 base64로 인코딩"""
    try:
        return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        st.error(f"❌ 이미지 인코딩 오류: {str(e)}")
        return None


def analyze_all_images_with_vision(image_files_with_data):
    """GPT-4o Vision을 사용하여 모든 이미지를 일괄 분석"""
    try:
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
"""

        message_content = [{"type": "text", "text": analysis_prompt}]

        # 모든 이미지 추가
        for idx, (filename, image_data) in enumerate(image_files_with_data, 1):
            if image_data:
                message_content.append({
                    "type": "text",
                    "text": f"[사진 {idx}: {filename}]"
                })
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                })

        # API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message_content}],
            max_tokens=2000
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"분석 오류: {str(e)}"


# UI
st.set_page_config(page_title="AI 사진첩 해결사", page_icon="📸", layout="wide")
st.title("📸 나만의 AI 해결사: 스마트폰 사진첩 정리")
st.markdown("---")
st.write("사진을 업로드하면 AI가 자동으로 분석하여 삭제 여부를 제안해 드립니다.")

st.subheader("📤 사진 업로드")
uploaded_files = st.file_uploader(
    "정리할 사진들을 선택해주세요 (JPG, PNG, JPEG):",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.markdown("---")
    st.subheader(f"📋 업로드된 사진 ({len(uploaded_files)}장)")

    cols = st.columns(min(len(uploaded_files), 5))
    for idx, uploaded_file in enumerate(uploaded_files):
        with cols[idx % 5]:
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption=f"사진 {idx + 1}", use_column_width=True)
            except Exception as e:
                st.error(f"이미지 로드 실패: {str(e)}")

    st.markdown("---")

    if st.button("🔍 전체 분석 시작", use_container_width=True):
        with st.spinner("AI가 모든 사진을 분석 중입니다..."):
            image_files_with_data = []
            for uploaded_file in uploaded_files:
                uploaded_file.seek(0)
                image_data = encode_image_to_base64(uploaded_file)
                if image_data:
                    image_files_with_data.append((uploaded_file.name, image_data))

            if image_files_with_data:
                analysis_result = analyze_all_images_with_vision(image_files_with_data)
                st.markdown("---")
                st.subheader("📊 분석 결과")
                st.markdown(analysis_result)

                st.download_button(
                    label="📥 분석 결과 다운로드",
                    data=analysis_result,
                    file_name="photo_analysis_result.txt",
                    mime="text/plain"
                )
            else:
                st.error("유효한 이미지를 찾을 수 없습니다.")
else:
    st.info("💡 사진을 업로드하면 AI가 자동으로 분석을 시작합니다.")

st.markdown("---")
st.info("**사용 방법:** 사진을 업로드하고 '전체 분석 시작' 버튼을 클릭하세요.")
