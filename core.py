# core.py
import os
import json
import logging
from typing import Optional, Dict, Any, List

from opencc import OpenCC

# ==============================
# Logging 設定
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ==============================
# 資料庫路徑與同義詞對應
# ==============================
DB_PATH = os.path.join(os.path.dirname(__file__), "medical_knowledge.json")

SYNONYMS: Dict[str, List[str]] = {
    "肚子痛": ["胃痛", "腹痛", "肚悶", "腸胃不舒服"],
    "拉肚子": ["腹瀉", "大便水", "便稀", "跑廁所"],
    "頭暈": ["暈眩", "暈頭轉向", "眼花"],
}

# ==============================
# 讀取醫療知識庫
# ==============================
def load_medical_db() -> Dict[str, Any]:
    """安全讀取 JSON 知識庫，若失敗則回傳空字典"""
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logging.error(f"無法讀取醫療知識庫: {e}")
    else:
        logging.warning("找不到 medical_knowledge.json，將使用空白知識庫")
    return {}

medical_db: Dict[str, Any] = load_medical_db()

def fallback_response(user_input: str) -> str:
    """
    提供在知識庫與模型都失敗時的安撫性回應。
    """
    template = (
        f"您好～我了解您提到「{user_input}」，"
        "雖然我這裡沒有找到確切的建議，但請您不用太擔心。"
        "先多喝點溫開水，好好休息。"
        "如果症狀持續或讓您很不舒服，建議和家人一起去看醫師。"
        "如果還有其他不舒服，也可以再問我喔，我會陪著您 😊"
    )
    return template
# ==============================
# OpenCC：簡轉繁
# ==============================
cc = OpenCC("s2t")

def to_traditional(text: str) -> str:
    """將輸入轉換為繁體中文"""
    return cc.convert(text)

# ==============================
# 偵測簡體字
# ==============================
SIMPLIFIED_CHARS = set("后发为亿仅厉压妈属层厂广庆录觉")

def contains_simplified_chinese(text: str) -> bool:
    """檢查字串是否含簡體字"""
    return any(c in SIMPLIFIED_CHARS for c in text)

# ==============================
# 回應內容品質檢查
# ==============================
DANGER_WORDS = {
    "癌", "腫瘤", "敗血", "末期", "惡性", "器官衰竭",
    "死亡", "截肢", "痙攣", "糖尿病", "腎病變", "慢性病", "病發", "惡化"
}
NONSENSE_WORDS = {"滴水", "肝膜病", "寄生處機", "胎婦與孕婦的危險"}

def is_valid_response(text: str, min_length: int = 50) -> bool:
    """
    檢查模型或知識庫回應是否合格。
    - 不含危險詞
    - 不含無意義內容
    - 不含簡體字
    - 字數足夠
    """
    if not text or not isinstance(text, str):
        return False
    if any(w in text for w in DANGER_WORDS | NONSENSE_WORDS):
        logging.warning("回應含有危險或無意義詞彙")
        return False
    if contains_simplified_chinese(text):
        logging.warning("回應含有簡體字")
        return False
    if len(text.strip()) < min_length:
        logging.warning("回應過短，可能無法幫助使用者")
        return False
    return True

# ==============================
# 資料庫查詢（含同義詞）
# ==============================
def lookup_medical_db(user_input: str) -> Optional[str]:
    """
    根據使用者輸入查詢知識庫，並組裝建議回應。
    Args:
        user_input (str): 使用者輸入內容
    Returns:
        str | None: 找到時回傳格式化文字，否則 None
    """
    if not user_input:
        return None

    user_input = user_input.strip()
    for key, entry in medical_db.items():
        terms = [key] + SYNONYMS.get(key, [])
        if any(term in user_input for term in terms):
            return format_response(entry)
    return None

def format_response(entry: Dict[str, Any]) -> str:
    """
    將知識庫的內容格式化成清單式回應。
    """
    sections = [
        ("1. 可能原因：", entry.get("possible_causes", [])),
        ("2. 在家可以怎麼做：", entry.get("self_care", [])),
        ("3. 什麼時候需要看醫生：", entry.get("when_to_see_doctor", [])),
    ]

    lines = []
    for title, items in sections:
        lines.append(title)
        if items:
            lines.extend(f"   - {item}" for item in items)
        else:
            lines.append("   - （暫無資料）")

    lines.append("4. 鼓勵的話：")
    lines.append(f"   - {entry.get('encouragement', '請多注意休息喔！')}")
    return "\n".join(lines)
