"""
メモリ最適化モジュール
長い動画の処理時のメモリ使用量を最適化
"""

import os
import gc
import psutil
import logging
from typing import Optional, Dict, Any
import numpy as np
import librosa
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class MemoryOptimizer:
    """メモリ使用量を最適化するクラス"""
    
    def __init__(self, max_memory_usage: float = 0.8):
        """
        Args:
            max_memory_usage: 最大メモリ使用率（0.8 = 80%）
        """
        self.max_memory_usage = max_memory_usage
        self.process = psutil.Process()
    
    def get_memory_usage(self) -> Dict[str, float]:
        """現在のメモリ使用量を取得"""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # MB
            "vms_mb": memory_info.vms / 1024 / 1024,  # MB
            "percent": memory_percent
        }
    
    def check_memory_limit(self) -> bool:
        """メモリ使用量が制限を超えているかチェック"""
        memory_usage = self.get_memory_usage()
        return memory_usage["percent"] > (self.max_memory_usage * 100)
    
    def force_garbage_collection(self):
        """強制的にガベージコレクションを実行"""
        collected = gc.collect()
        logger.info(f"ガベージコレクション実行: {collected} オブジェクトを回収")
    
    @contextmanager
    def memory_monitor(self, operation_name: str):
        """メモリ使用量を監視するコンテキストマネージャー"""
        initial_memory = self.get_memory_usage()
        logger.info(f"{operation_name} 開始 - メモリ使用量: {initial_memory['rss_mb']:.1f}MB")
        
        try:
            yield
        finally:
            final_memory = self.get_memory_usage()
            memory_diff = final_memory['rss_mb'] - initial_memory['rss_mb']
            logger.info(f"{operation_name} 完了 - メモリ増加: {memory_diff:+.1f}MB")
            
            # メモリ使用量が高い場合はガベージコレクション
            if final_memory['percent'] > 70:
                self.force_garbage_collection()

class ChunkedAudioProcessor:
    """チャンク分割による音声処理"""
    
    def __init__(self, chunk_duration: float = 30.0, overlap: float = 5.0):
        """
        Args:
            chunk_duration: チャンクの長さ（秒）
            overlap: オーバーラップ時間（秒）
        """
        self.chunk_duration = chunk_duration
        self.overlap = overlap
    
    def process_audio_in_chunks(self, audio_file_path: str, 
                               sample_rate: int = 22050) -> Dict[str, Any]:
        """
        音声ファイルをチャンク分割して処理
        
        Args:
            audio_file_path: 音声ファイルパス
            sample_rate: サンプルレート
        
        Returns:
            処理結果の辞書
        """
        results = {
            "chunks": [],
            "overall_analysis": {},
            "memory_usage": []
        }
        
        # 音声ファイルの長さを取得
        duration = librosa.get_duration(path=audio_file_path)
        
        # チャンク分割
        chunk_samples = int(self.chunk_duration * sample_rate)
        overlap_samples = int(self.overlap * sample_rate)
        
        for i, start_time in enumerate(np.arange(0, duration, self.chunk_duration - self.overlap)):
            end_time = min(start_time + self.chunk_duration, duration)
            
            # チャンクを読み込み
            y_chunk, sr = librosa.load(
                audio_file_path, 
                sr=sample_rate,
                offset=start_time,
                duration=end_time - start_time
            )
            
            # チャンク分析
            chunk_analysis = self._analyze_chunk(y_chunk, sr, start_time)
            results["chunks"].append(chunk_analysis)
            
            # メモリ使用量を記録
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
            results["memory_usage"].append(memory_usage)
        
        # 全体分析を統合
        results["overall_analysis"] = self._integrate_chunk_results(results["chunks"])
        
        return results
    
    def _analyze_chunk(self, y: np.ndarray, sr: int, start_time: float) -> Dict[str, Any]:
        """個別チャンクの分析"""
        # RMS（音量）分析
        rms = librosa.feature.rms(y=y)[0]
        
        # ピッチ分析
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_mean = np.mean(pitches, axis=0)
        
        return {
            "start_time": start_time,
            "duration": len(y) / sr,
            "volume": {
                "mean": float(np.mean(rms)),
                "max": float(np.max(rms)),
                "min": float(np.min(rms)),
                "std": float(np.std(rms))
            },
            "pitch": {
                "mean": float(np.mean(pitch_mean)),
                "std": float(np.std(pitch_mean))
            }
        }
    
    def _integrate_chunk_results(self, chunks: list) -> Dict[str, Any]:
        """チャンク結果を統合"""
        if not chunks:
            return {}
        
        # 全体の統計を計算
        all_volumes = [chunk["volume"]["mean"] for chunk in chunks]
        all_pitches = [chunk["pitch"]["mean"] for chunk in chunks]
        
        return {
            "total_duration": sum(chunk["duration"] for chunk in chunks),
            "volume_analysis": {
                "mean": float(np.mean(all_volumes)),
                "max": float(np.max(all_volumes)),
                "min": float(np.min(all_volumes)),
                "std": float(np.std(all_volumes))
            },
            "pitch_analysis": {
                "mean": float(np.mean(all_pitches)),
                "std": float(np.std(all_pitches))
            },
            "chunk_count": len(chunks)
        }

class TemporaryFileManager:
    """一時ファイルの管理"""
    
    def __init__(self):
        self.temp_files = []
    
    def add_temp_file(self, file_path: str):
        """一時ファイルを登録"""
        self.temp_files.append(file_path)
    
    def cleanup_all(self):
        """全ての一時ファイルを削除"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"一時ファイル削除: {file_path}")
            except Exception as e:
                logger.warning(f"一時ファイル削除失敗: {file_path} - {e}")
        
        self.temp_files.clear()
    
    def __del__(self):
        """デストラクタでクリーンアップ"""
        self.cleanup_all()

# グローバルインスタンス
memory_optimizer = MemoryOptimizer()
temp_file_manager = TemporaryFileManager() 