"""
包括的エラーハンドリングシステム
アプリケーション全体でのエラー管理を統一
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable
from fastapi import HTTPException
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """エラータイプの定義"""
    API_KEY_INVALID = "api_key_invalid"
    DOWNLOAD_FAILED = "download_failed"
    AUDIO_PROCESSING_FAILED = "audio_processing_failed"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"

class ErrorHandler:
    """包括的エラーハンドリングクラス"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_callbacks = {}
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        エラーを処理し、適切なレスポンスを返す
        
        Args:
            error: 発生したエラー
            context: エラーコンテキスト
        
        Returns:
            エラー情報の辞書
        """
        error_type = self._classify_error(error)
        error_info = self._create_error_info(error, error_type, context)
        
        # エラーカウントを更新
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # ログ出力
        self._log_error(error_info)
        
        # コールバック実行
        if error_type in self.error_callbacks:
            self.error_callbacks[error_type](error_info)
        
        return error_info
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """エラーを分類"""
        error_str = str(error).lower()
        
        if "api key" in error_str or "unauthorized" in error_str:
            return ErrorType.API_KEY_INVALID
        elif "download" in error_str or "yt-dlp" in error_str:
            return ErrorType.DOWNLOAD_FAILED
        elif "audio" in error_str or "librosa" in error_str:
            return ErrorType.AUDIO_PROCESSING_FAILED
        elif "memory" in error_str or "out of memory" in error_str:
            return ErrorType.MEMORY_LIMIT_EXCEEDED
        elif "timeout" in error_str:
            return ErrorType.TIMEOUT_ERROR
        elif "network" in error_str or "connection" in error_str:
            return ErrorType.NETWORK_ERROR
        elif "validation" in error_str or "invalid" in error_str:
            return ErrorType.VALIDATION_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _create_error_info(self, error: Exception, error_type: ErrorType, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """エラー情報を作成"""
        error_info = {
            "error_type": error_type.value,
            "error_message": str(error),
            "error_class": error.__class__.__name__,
            "traceback": traceback.format_exc(),
            "context": context or {},
            "timestamp": self._get_timestamp()
        }
        
        # エラータイプ別の詳細情報を追加
        if error_type == ErrorType.API_KEY_INVALID:
            error_info["suggestion"] = "APIキーを確認してください"
            error_info["http_status"] = 401
        elif error_type == ErrorType.DOWNLOAD_FAILED:
            error_info["suggestion"] = "動画URLを確認してください"
            error_info["http_status"] = 400
        elif error_type == ErrorType.MEMORY_LIMIT_EXCEEDED:
            error_info["suggestion"] = "動画が長すぎます。短い動画を試してください"
            error_info["http_status"] = 413
        elif error_type == ErrorType.TIMEOUT_ERROR:
            error_info["suggestion"] = "しばらく待ってから再試行してください"
            error_info["http_status"] = 408
        else:
            error_info["suggestion"] = "システムエラーが発生しました"
            error_info["http_status"] = 500
        
        return error_info
    
    def _log_error(self, error_info: Dict[str, Any]):
        """エラーをログに出力"""
        log_message = f"エラー発生: {error_info['error_type']} - {error_info['error_message']}"
        
        if error_info["error_type"] in ["api_key_invalid", "validation_error"]:
            logger.warning(log_message)
        else:
            logger.error(log_message)
            logger.debug(f"詳細: {error_info['traceback']}")
    
    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def register_error_callback(self, error_type: ErrorType, callback: Callable):
        """エラーコールバックを登録"""
        self.error_callbacks[error_type] = callback
    
    def get_error_statistics(self) -> Dict[str, int]:
        """エラー統計を取得"""
        return self.error_counts.copy()

class ValidationError(Exception):
    """バリデーションエラー"""
    pass

class AudioProcessingError(Exception):
    """音声処理エラー"""
    pass

class DownloadError(Exception):
    """ダウンロードエラー"""
    pass

def create_http_exception(error_info: Dict[str, Any]) -> HTTPException:
    """HTTPExceptionを作成"""
    return HTTPException(
        status_code=error_info["http_status"],
        detail={
            "error_type": error_info["error_type"],
            "message": error_info["error_message"],
            "suggestion": error_info["suggestion"]
        }
    )

def validate_youtube_url(url: str) -> bool:
    """YouTube URLの検証"""
    import re
    
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+'
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)

def validate_api_key(api_key: str, api_type: str) -> bool:
    """APIキーの検証"""
    if not api_key:
        return False
    
    # 基本的な形式チェック
    if api_type == "youtube":
        return len(api_key) >= 30 and api_key.startswith("AIza")
    elif api_type == "gemini":
        return len(api_key) >= 20
    
    return True

# グローバルエラーハンドラー
error_handler = ErrorHandler()

# エラーコールバックの登録例
def memory_error_callback(error_info: Dict[str, Any]):
    """メモリエラー時のコールバック"""
    logger.warning("メモリ使用量が制限を超えました。ガベージコレクションを実行します")
    import gc
    gc.collect()

error_handler.register_error_callback(ErrorType.MEMORY_LIMIT_EXCEEDED, memory_error_callback) 