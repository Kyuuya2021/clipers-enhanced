import os
from dotenv import load_dotenv # type: ignore
import logging
from typing import Optional

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .envファイルを読み込み
load_dotenv()

# APIキーの設定
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_youtube_api_key() -> Optional[str]:
    """YouTube APIキーを取得（環境変数のみ）"""
    if not YOUTUBE_API_KEY:
        logger.warning("YouTube API key not found in environment variables")
    return YOUTUBE_API_KEY

def get_gemini_api_key() -> Optional[str]:
    """Gemini APIキーを取得（環境変数のみ）"""
    if not GEMINI_API_KEY:
        logger.warning("Gemini API key not found in environment variables")
    return GEMINI_API_KEY

def validate_api_keys() -> dict:
    """APIキーの有効性を検証"""
    validation_result = {
        "youtube_api_key": bool(YOUTUBE_API_KEY),
        "gemini_api_key": bool(GEMINI_API_KEY),
        "all_valid": bool(YOUTUBE_API_KEY and GEMINI_API_KEY)
    }
    
    if not validation_result["all_valid"]:
        logger.error("API keys validation failed")
    
    return validation_result 