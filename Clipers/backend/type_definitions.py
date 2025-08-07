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