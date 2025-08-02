import logging
import requests
from typing import Optional, Dict, Any
from core import to_traditional, is_valid_response

# ===== Ollama API 設定 =====
MODEL = "qwen:1.8b-chat"
OLLAMA_URL_CLI = "http://localhost:11434/api/chat"
OLLAMA_URL_WEB = "http://localhost:11434/api/generate"

# ===== Fallback Hint =====
FALLBACK_HINT = (
    "請用更簡單的方式說明，避免提到專業名詞與可怕疾病，"
    "語氣溫和，針對年長者，務必使用正體中文。"
)

# ===== Logging 設定 =====
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ===== Prompt 建立函式 =====
def build_cli_prompt(user_question: str) -> str:
    """產生適合 CLI 的提示語"""
    return f"""你是一位貼心的健康小幫手，專門幫助台灣的長輩理解身體小狀況。
請針對以下提問，用溫和、簡單、白話的語氣說明，千萬不要提到癌症、腎衰竭、死亡等詞語。
請使用正體中文。

請遵照以下格式回答：
1. 可能原因（請用「有可能是…也可能是…」的語氣，避免肯定診斷）
2. 在家可以怎麼做（列 2~3 點，像是「多喝溫水」、「注意休息」）
3. 什麼時候需要看醫生（舉 2 個簡單例子）
4. 溫暖鼓勵語

以「您好～」開頭，「如果還有其他不舒服，也可以再問我喔，我會陪著您 😊」結尾。

問題如下：
「{user_question}」
"""

def build_web_prompt(user_input: str) -> str:
    """產生適合 Web 的提示語"""
    return f"""你是一位貼心的中文健康助理，請用溫暖、親切、容易懂的繁體中文，幫助長者理解他們的身體狀況。
請避免使用嚇人的醫學術語，並保持語氣溫和。
請以「您好～」開頭，以「如果還有其他不舒服，也可以再問我喔，我會陪著您 😊」結尾。

問題：
「{user_input}」
"""

# ===== 通用 POST 請求 =====
def _post_request(url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """通用的 POST 請求處理，避免重複程式碼"""
    try:
        logger.info(f"向 Ollama 請求: {url}")
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API 錯誤: {e}")
        return None

# ===== CLI 模式呼叫 =====
def query_ollama_cli(prompt: str, use_fallback: bool = False) -> str:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    response = _post_request(OLLAMA_URL_CLI, payload)
    if response:
        answer = response.get("message", {}).get("content", "").strip()
        if is_valid_response(answer):
            return to_traditional(answer)
        if not use_fallback:
            logger.warning("回應不符合標準，嘗試使用 fallback hint")
            modified_prompt = prompt + "\n\n" + FALLBACK_HINT
            return query_ollama_cli(modified_prompt, use_fallback=True)
        else:
            logger.error("fallback 仍不合格，回傳預設訊息")
            return "抱歉，我目前無法給出合適的建議，請諮詢醫生。"
    return "⚠️ 系統錯誤，請稍後再試。"

# ===== Web 模式呼叫 =====
def query_ollama_web(user_input: str, use_fallback: bool = False) -> str:
    prompt = build_web_prompt(user_input)
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }
    response = _post_request(OLLAMA_URL_WEB, payload)
    if response:
        answer = response.get("response", "").strip()
        if is_valid_response(answer):
            return to_traditional(answer)
        if not use_fallback:
            logger.warning("回應不符合標準，嘗試使用 fallback hint")
            modified_input = user_input + "。" + FALLBACK_HINT
            return query_ollama_web(modified_input, use_fallback=True)
        else:
            logger.error("fallback 仍不合格，回傳預設訊息")
            return "抱歉，我目前無法給出合適的建議，請諮詢醫生。"
    return "⚠️ 系統錯誤，請稍後再試。"
