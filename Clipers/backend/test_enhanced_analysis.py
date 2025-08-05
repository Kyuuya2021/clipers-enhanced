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