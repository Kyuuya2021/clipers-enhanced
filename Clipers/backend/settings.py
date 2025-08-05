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