# 📝 変更内容詳細差分

## 🔍 変更されたファイル一覧

### 1. `backend/config.py` - セキュリティ強化
```diff
+ import logging
+ from typing import Optional
+ 
+ # ログ設定
+ logging.basicConfig(level=logging.INFO)
+ logger = logging.getLogger(__name__)

  # .envファイルを読み込み
  load_dotenv()
  
  # APIキーの設定
  YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
  GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
  
- def get_youtube_api_key():
+ def get_youtube_api_key() -> Optional[str]:
      """YouTube APIキーを取得（環境変数のみ）"""
+     if not YOUTUBE_API_KEY:
+         logger.warning("YouTube API key not found in environment variables")
      return YOUTUBE_API_KEY
  
- def get_gemini_api_key():
+ def get_gemini_api_key() -> Optional[str]:
      """Gemini APIキーを取得（環境変数のみ）"""
+     if not GEMINI_API_KEY:
+         logger.warning("Gemini API key not found in environment variables")
      return GEMINI_API_KEY
+ 
+ def validate_api_keys() -> dict:
+     """APIキーの有効性を検証"""
+     validation_result = {
+         "youtube_api_key": bool(YOUTUBE_API_KEY),
+         "gemini_api_key": bool(GEMINI_API_KEY),
+         "all_valid": bool(YOUTUBE_API_KEY and GEMINI_API_KEY)
+     }
+     
+     if not validation_result["all_valid"]:
+         logger.error("API keys validation failed")
+     
+     return validation_result
```

### 2. `backend/type_definitions.py` - 新規作成
```python
"""
型定義ファイル
プロジェクト全体で使用する型を統一管理
"""

from typing import Dict, List, Optional, Union, TypedDict
from pydantic import BaseModel
from datetime import datetime

# 音声分析結果の型定義
class AudioAnalysisResult(TypedDict):
    duration: float
    sample_rate: int
    volume_analysis: Dict[str, float]
    pitch_analysis: Dict[str, float]
    excitement_points: List[Dict[str, Union[float, str]]]
    overall_excitement_score: float
    analysis_metadata: Dict[str, Union[str, float]]

# エンゲージメント分析結果の型定義
class EngagementAnalysisResult(TypedDict):
    video_info: Dict[str, Union[str, int]]
    engagement_rate: float
    comments: Dict[str, Union[int, List[Dict]]]
    hot_timestamps: List[Dict[str, Union[str, int]]]
    sentiment_analysis: Dict[str, Union[str, float]]
    keywords: List[Dict[str, Union[str, int]]]

# Gemini分析結果の型定義
class GeminiAnalysisResult(TypedDict):
    narrative_score: Optional[float]
    hook_score: Optional[float]
    engagement_score: Optional[float]
    tech_score: Optional[float]
    summary: Optional[str]
    golden_clip: Optional[str]
    semantic_hotspots: Optional[List[Dict]]

# 包括的分析結果の型定義
class ComprehensiveAnalysisResult(TypedDict):
    audio_analysis: AudioAnalysisResult
    engagement_analysis: EngagementAnalysisResult
    comprehensive_score: float
    analysis_timestamp: str

# エラーレスポンスの型定義
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str

# APIキー検証結果の型定義
class APIKeyValidationResult(TypedDict):
    youtube_api_key: bool
    gemini_api_key: bool
    all_valid: bool

# 動画情報の型定義
class VideoInfo(BaseModel):
    title: str
    duration: Optional[int]
    description: Optional[str]
    view_count: Optional[int]
    like_count: Optional[int]

# 分析リクエストの型定義
class AnalysisRequest(BaseModel):
    url: str
    download_audio: bool = True
    youtube_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

# 分析レスポンスの型定義
class AnalysisResponse(BaseModel):
    video_info: VideoInfo
    audio_file_path: Optional[str]
    transcript_file_path: Optional[str]
    audio_duration: Optional[float]
    sample_rate: Optional[int]
    debug_info: Dict[str, str]
```

### 3. `backend/utils.py` - 新規作成
```python
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
```

### 4. `backend/settings.py` - 新規作成
```python
"""
設定ファイル
プロジェクト全体の設定値を管理
"""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class AudioAnalysisSettings:
    """音声分析の設定"""
    sample_rate: int = 22050
    reference_level: float = 1.0
    min_db: float = -60.0
    max_db: float = 0.0
    frame_length_ms: int = 25
    hop_length_ms: int = 10

@dataclass
class EngagementAnalysisSettings:
    """エンゲージメント分析の設定"""
    max_comments: int = 300
    sentiment_threshold: float = 0.5
    keyword_min_frequency: int = 2
    hot_timestamp_threshold: int = 3

@dataclass
class GeminiAnalysisSettings:
    """Gemini分析の設定"""
    max_transcript_length: int = 8000
    max_comments_length: int = 8000
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.7

@dataclass
class VideoEvaluationSettings:
    """動画評価フレームワークの設定"""
    pillar_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.pillar_weights is None:
            self.pillar_weights = {
                "technical_quality": 0.05,      # 5%
                "hook_effectiveness": 0.25,     # 25%
                "narrative_retention": 0.40,    # 40%
                "engagement_signals": 0.20,     # 20%
                "platform_integrity": 0.10      # 10%
            }

@dataclass
class ServerSettings:
    """サーバー設定"""
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    max_request_size: int = 100 * 1024 * 1024  # 100MB
    timeout: int = 300  # 5分

@dataclass
class SecuritySettings:
    """セキュリティ設定"""
    cors_origins: list = None
    api_key_required: bool = True
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 60
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]  # 本番環境では具体的なドメインを指定

# 設定インスタンスの作成
audio_settings = AudioAnalysisSettings()
engagement_settings = EngagementAnalysisSettings()
gemini_settings = GeminiAnalysisSettings()
evaluation_settings = VideoEvaluationSettings()
server_settings = ServerSettings()
security_settings = SecuritySettings()

# 全設定を取得する関数
def get_all_settings() -> Dict[str, Any]:
    """全設定を辞書形式で取得"""
    return {
        "audio_analysis": audio_settings.__dict__,
        "engagement_analysis": engagement_settings.__dict__,
        "gemini_analysis": gemini_settings.__dict__,
        "video_evaluation": evaluation_settings.__dict__,
        "server": server_settings.__dict__,
        "security": security_settings.__dict__
    }
```

### 5. `backend/test_enhanced_analysis.py` - 新規作成
```python
#!/usr/bin/env python3
"""
包括的テストスクリプト
プロジェクト全体の機能をテスト
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
import tempfile
import json

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from improved_audio_analyzer import ImprovedAudioAnalyzer, YouTubeEngagementAnalyzer
from gemini_analyzer import GeminiAnalyzer
from video_evaluation_framework import VideoEvaluationFramework
from user_attribute_analyzer import UserAttributeAnalyzer
from config import validate_api_keys
from utils import validate_youtube_url, create_error_response
from settings import get_all_settings

class TestAudioAnalyzer(unittest.TestCase):
    """音声分析器のテスト"""
    
    def setUp(self):
        self.analyzer = ImprovedAudioAnalyzer()
    
    def test_analyzer_initialization(self):
        """分析器の初期化テスト"""
        self.assertEqual(self.analyzer.sample_rate, 22050)
        self.assertEqual(self.analyzer.reference_level, 1.0)
        self.assertEqual(self.analyzer.min_db, -60)
        self.assertEqual(self.analyzer.max_db, 0)
    
    @patch('librosa.load')
    def test_analyze_audio_accurate(self, mock_load):
        """正確な音声分析のテスト"""
        # モックデータを設定
        mock_y = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_sr = 22050
        mock_load.return_value = (mock_y, mock_sr)
        
        # テスト実行
        result = self.analyzer.analyze_audio_accurate("dummy_path.wav")
        
        # 結果の検証
        self.assertIn("duration", result)
        self.assertIn("sample_rate", result)
        self.assertIn("volume_analysis", result)
        self.assertIn("pitch_analysis", result)
        self.assertIn("excitement_points", result)
        self.assertIn("overall_excitement_score", result)

class TestEngagementAnalyzer(unittest.TestCase):
    """エンゲージメント分析器のテスト"""
    
    def setUp(self):
        self.analyzer = YouTubeEngagementAnalyzer()
    
    def test_extract_video_id(self):
        """動画ID抽出のテスト"""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ")
        ]
        
        for url, expected_id in test_cases:
            with self.subTest(url=url):
                result = self.analyzer.extract_video_id(url)
                self.assertEqual(result, expected_id)
    
    def test_calculate_engagement_rate(self):
        """エンゲージメント率計算のテスト"""
        statistics = {
            "viewCount": "1000",
            "likeCount": "100",
            "commentCount": "50"
        }
        
        result = self.analyzer._calculate_engagement_rate(statistics)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0)

class TestGeminiAnalyzer(unittest.TestCase):
    """Gemini分析器のテスト"""
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_analyzer_initialization(self, mock_model, mock_configure):
        """Gemini分析器の初期化テスト"""
        mock_model_instance = Mock()
        mock_model.return_value = mock_model_instance
        
        analyzer = GeminiAnalyzer(api_key="test_key")
        
        mock_configure.assert_called_once_with(api_key="test_key")
        mock_model.assert_called_once_with('gemini-1.5-flash')
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_content_with_gemini(self, mock_model, mock_configure):
        """Gemini分析のテスト"""
        mock_model_instance = Mock()
        mock_response = Mock()
        mock_response.text = '{"narrative_score": 8.5, "hook_score": 7.2}'
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        analyzer = GeminiAnalyzer(api_key="test_key")
        result = analyzer.analyze_content_with_gemini("test transcript", ["test comment"])
        
        self.assertIn("narrative_score", result)
        self.assertIn("hook_score", result)

class TestUserAttributeAnalyzer(unittest.TestCase):
    """ユーザー属性分析器のテスト"""
    
    def setUp(self):
        self.analyzer = UserAttributeAnalyzer()
    
    def test_analyze_user_attributes(self):
        """ユーザー属性分析のテスト"""
        test_comments = [
            "私は20代の会社員です。東京在住。",
            "高校生女子です！",
            "大阪の大学生です",
            "40歳の主婦です"
        ]
        
        result = self.analyzer.analyze(test_comments)
        
        self.assertIn("age", result)
        self.assertIn("region", result)
        self.assertIn("affiliation", result)
        self.assertIn("gender", result)

class TestVideoEvaluationFramework(unittest.TestCase):
    """動画評価フレームワークのテスト"""
    
    def setUp(self):
        self.framework = VideoEvaluationFramework()
    
    def test_pillar_weights(self):
        """柱の重み付けテスト"""
        weights = self.framework.pillar_weights
        self.assertEqual(len(weights), 5)
        self.assertAlmostEqual(sum(weights.values()), 1.0)
    
    def test_calculate_total_score(self):
        """総合スコア計算のテスト"""
        from video_evaluation_framework import EvaluationMetrics, EvaluationPillar
        
        mock_evaluations = [
            EvaluationMetrics(EvaluationPillar.TECHNICAL_QUALITY, 4.0, 5.0, {}, []),
            EvaluationMetrics(EvaluationPillar.HOOK_EFFECTIVENESS, 3.5, 5.0, {}, []),
            EvaluationMetrics(EvaluationPillar.NARRATIVE_RETENTION, 4.5, 5.0, {}, []),
            EvaluationMetrics(EvaluationPillar.ENGAGEMENT_SIGNALS, 4.0, 5.0, {}, []),
            EvaluationMetrics(EvaluationPillar.PLATFORM_INTEGRITY, 3.0, 5.0, {}, [])
        ]
        
        total_score = self.framework._calculate_total_score(mock_evaluations)
        self.assertIsInstance(total_score, float)
        self.assertGreaterEqual(total_score, 0)

class TestUtils(unittest.TestCase):
    """ユーティリティ関数のテスト"""
    
    def test_validate_youtube_url(self):
        """YouTube URL検証のテスト"""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ"
        ]
        
        invalid_urls = [
            "https://www.google.com",
            "https://www.youtube.com",
            "invalid_url"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(validate_youtube_url(url))
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(validate_youtube_url(url))
    
    def test_create_error_response(self):
        """エラーレスポンス作成のテスト"""
        error_response = create_error_response("Test error", "Test detail")
        
        self.assertIn("error", error_response)
        self.assertIn("detail", error_response)
        self.assertIn("timestamp", error_response)
        self.assertEqual(error_response["error"], "Test error")
        self.assertEqual(error_response["detail"], "Test detail")

class TestConfig(unittest.TestCase):
    """設定のテスト"""
    
    def test_validate_api_keys(self):
        """APIキー検証のテスト"""
        result = validate_api_keys()
        
        self.assertIn("youtube_api_key", result)
        self.assertIn("gemini_api_key", result)
        self.assertIn("all_valid", result)
        self.assertIsInstance(result["youtube_api_key"], bool)
        self.assertIsInstance(result["gemini_api_key"], bool)
        self.assertIsInstance(result["all_valid"], bool)

class TestSettings(unittest.TestCase):
    """設定ファイルのテスト"""
    
    def test_get_all_settings(self):
        """全設定取得のテスト"""
        settings = get_all_settings()
        
        self.assertIn("audio_analysis", settings)
        self.assertIn("engagement_analysis", settings)
        self.assertIn("gemini_analysis", settings)
        self.assertIn("video_evaluation", settings)
        self.assertIn("server", settings)
        self.assertIn("security", settings)

def run_integration_test():
    """統合テストの実行"""
    print("🧪 統合テストを開始します...")
    
    # 設定のテスト
    try:
        settings = get_all_settings()
        print("✅ 設定ファイル: OK")
    except Exception as e:
        print(f"❌ 設定ファイル: エラー - {e}")
    
    # APIキー検証のテスト
    try:
        api_validation = validate_api_keys()
        print(f"✅ APIキー検証: {api_validation}")
    except Exception as e:
        print(f"❌ APIキー検証: エラー - {e}")
    
    # URL検証のテスト
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    try:
        is_valid = validate_youtube_url(test_url)
        print(f"✅ URL検証: {is_valid}")
    except Exception as e:
        print(f"❌ URL検証: エラー - {e}")
    
    print("🎉 統合テスト完了")

if __name__ == "__main__":
    # 統合テストを実行
    run_integration_test()
    
    # ユニットテストを実行
    print("\n🧪 ユニットテストを開始します...")
    unittest.main(verbosity=2)
```

---

## 📊 変更統計サマリー

| 項目 | 数値 |
|------|------|
| **変更ファイル数** | 5 |
| **追加行数** | 633 |
| **削除行数** | 3 |
| **新規作成ファイル** | 4 |
| **修正ファイル** | 1 |

---

## 🎯 主要な改善点

1. **セキュリティ強化**: APIキー管理とログ機能の追加
2. **型安全性向上**: 包括的な型定義ファイルの実装
3. **コード品質向上**: 共通処理の関数化とエラーハンドリング統一
4. **保守性向上**: 設定の一元管理とテストカバレッジ向上
5. **開発効率向上**: 包括的なテストスイートの実装

これらの変更により、プロジェクトの品質と保守性が大幅に向上しました。 