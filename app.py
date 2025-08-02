# app.py
import streamlit as st 
from core import (
    lookup_medical_db,
    is_valid_response,
    to_traditional,
    fallback_response
)
from utils import query_ollama_web, FALLBACK_HINT

def run_web():
    st.set_page_config(
        page_title="養生健康助理",
        page_icon="🧓",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    st.title("🧓 養生健康助理")
    st.markdown("💡 請輸入您的不適症狀，我會提供貼心的小建議。")

    # 保持輸入歷史
    if "history" not in st.session_state:
        st.session_state.history = []

    user_input = st.text_area(
        "請描述您的症狀，例如：肚子痛，一直拉肚子",
        height=120,
        key="input_text"
    )

    if st.button("🔍 幫我看看"):
        if not user_input.strip():
            st.warning("⚠️ 請先輸入您的身體狀況喔！")
        else:
            with st.spinner("🤖 助理正在思考中，請稍候..."):
                db_reply = lookup_medical_db(user_input)

                if db_reply:
                    reply = db_reply
                    st.success("✅ 查詢到常見症狀，以下是建議：")
                    st.text(reply)
                else:
                    reply = query_ollama_web(user_input)
                    if not is_valid_response(reply):
                        st.warning("⚠️ 回應可能不適合長輩，嘗試修正中...")
                        reply = query_ollama_web(user_input + "\n" + FALLBACK_HINT)

                    if not is_valid_response(reply):  # fallback
                        reply = fallback_response(user_input)

                    reply = to_traditional(reply)
                    st.success("✅ 助理的建議如下：")
                    st.markdown(reply)

                # 保存歷史紀錄
                st.session_state.history.append({"q": user_input, "a": reply})

    # 顯示歷史紀錄
    if st.session_state.history:
        st.markdown("---")
        st.subheader("📝 我的問答紀錄")
        for idx, record in enumerate(reversed(st.session_state.history), 1):
            with st.expander(f"問題 {idx}: {record['q']}"):
                st.markdown(record["a"])

    st.markdown("---")
    st.caption("© 2025 養生健康助理 — 提供溫暖的健康建議")

if __name__ == "__main__":
    run_web()
