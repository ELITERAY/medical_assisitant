# cli.py
import sys
import time
import logging
from core import (
    lookup_medical_db,
    is_valid_response,
    to_traditional,
    fallback_response
)
from utils import build_cli_prompt, query_ollama_cli, FALLBACK_HINT

# Logging 設定
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def run_cli():
    print("=== 長照健康助理 (CLI) 已啟動 ===\n")
    print("小提醒：輸入 exit 可隨時離開。\n")

    while True:
        try:
            question = input("請輸入養生問題（輸入 exit 離開）：\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 偵測到中斷，系統已結束。")
            break

        if not question:
            print("⚠️ 請輸入問題內容，不要留空。\n")
            continue

        if question.lower() == "exit":
            print("感謝使用，祝您健康平安～")
            break

        # 查詢本地知識庫
        db_reply = lookup_medical_db(question)
        if db_reply:
            print("\n✅ 資料庫結果：")
            print(db_reply)
            print("-" * 40)
            continue

        # 呼叫模型
        prompt = build_cli_prompt(question)
        print("\n🤖 模型處理中，請稍候...\n")
        time.sleep(0.5)
        reply = query_ollama_cli(prompt)

        # 品質檢查與 fallback
        if not is_valid_response(reply):
            logger.warning("回應不合格，將加入 fallback hint 重新請求")
            print("⚠️ 偵測到不適合長輩的內容，嘗試重新修正...\n")
            reply = query_ollama_cli(prompt + "\n" + FALLBACK_HINT)

        if not is_valid_response(reply):  # 模型還是沒給好答案
            reply = fallback_response(question)

        reply = to_traditional(reply)
        print("🤖 回應：")
        print(reply)
        print("-" * 40)

if __name__ == "__main__":
    try:
        run_cli()
    except Exception as e:
        logger.error(f"程式發生錯誤: {e}")
        sys.exit(1)
