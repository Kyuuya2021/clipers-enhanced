"""
共通ユーティリティ関数
プロジェクト全体で使用する共通処理を管理
"""

import os
import tempfile
import logging
from typing import Dict, Optional, Tuple
from fastapi import HTTPException
import yt_dlp
from config import get_youtube_api_key, get_gemini_api_key

logger = logging.getLogger(__name__)

def validate_api_keys_from_request(
    youtube_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None
) -> Tuple[str, str]:
    """
    APIキーの検証と取得
    
    Args:
        youtube_api_key: リクエストから送信されたYouTube APIキー
        gemini_api_key: リクエストから送信されたGemini APIキー
    
    Returns:
        Tuple[str, str]: (youtube_api_key, gemini_api_key)
    
    Raises:
        HTTPException: APIキーが無効な場合
    """
    # リクエスト優先、環境変数フォールバック
    final_youtube_key = youtube_api_key or get_youtube_api_key()
    final_gemini_key = gemini_api_key or get_gemini_api_key()
    
    if not final_youtube_key:
        raise HTTPException(
            status_code=400, 
            detail="有効なYouTube API keyが必要です（リクエストまたは環境変数YOUTUBE_API_KEY）"
        )
    
    if not final_gemini_key:
        raise HTTPException(
            status_code=400, 
            detail="有効なGemini API Keyが必要です（リクエストまたは環境変数GEMINI_API_KEY）"
        )
    
    return final_youtube_key, final_gemini_key

def download_video_with_subtitles(url: str) -> Dict:
    """
    動画と字幕をダウンロードする共通処理
    
    Args:
        url: YouTube動画URL
    
    Returns:
        Dict: ダウンロード結果
    """
    try:
        # 一時ディレクトリを作成
        temp_dir = tempfile.mkdtemp()
        logger.info(f"一時ディレクトリ作成: {temp_dir}")
        
        # yt-dlpの設定
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio[ext=webm]/bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ja', 'en'],
            'writesubtitlesformat': 'vtt',
            'writeautomaticsubformat': 'vtt',
        }
        
        # ダウンロード実行
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        # ファイルパスを取得
        audio_file = None
        transcript_file = None
        
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if file.endswith('.wav'):
                audio_file = file_path
            elif file.endswith('.vtt'):
                transcript_file = file_path
        
        return {
            'success': True,
            'temp_dir': temp_dir,
            'audio_file': audio_file,
            'transcript_file': transcript_file,
            'video_info': {
                'title': info.get('title', ''),
                'duration': info.get('duration'),
                'description': info.get('description', ''),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count')
            }
        }
        
    except Exception as e:
        logger.error(f"動画ダウンロードエラー: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def create_error_response(error_message: str, detail: Optional[str] = None) -> Dict:
    """
    統一されたエラーレスポンスを作成
    
    Args:
        error_message: エラーメッセージ
        detail: 詳細情報
    
    Returns:
        Dict: エラーレスポンス
    """
    from datetime import datetime
    
    return {
        "error": error_message,
        "detail": detail,
        "timestamp": datetime.now().isoformat()
    }

def cleanup_temp_files(temp_dir: str) -> None:
    """
    一時ファイルのクリーンアップ
    
    Args:
        temp_dir: 一時ディレクトリのパス
    """
    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"一時ディレクトリ削除: {temp_dir}")
    except Exception as e:
        logger.warning(f"一時ファイル削除エラー: {str(e)}")

def validate_youtube_url(url: str) -> bool:
    """
    YouTube URLの形式を検証
    
    Args:
        url: 検証するURL
    
    Returns:
        bool: 有効なYouTube URLかどうか
    """
    import re
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+'
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns) 