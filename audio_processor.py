import os
import tempfile
from moviepy import VideoFileClip

def extract_audio_from_video(video_path: str) -> str:
    """
    動画ファイルを受け取り、音声トラックを抽出してmp3として保存する。
    処理結果のファイルパスを返す。
    """
    try:
        videoclip = VideoFileClip(video_path)
        
        # 音声が存在しない動画への対応
        if videoclip.audio is None:
            raise ValueError("この動画には音声トラックがありません。")
            
        temp_dir = tempfile.gettempdir()
        audio_output_path = os.path.join(temp_dir, "extracted_audio.mp3")
        
        # mp3として出力（なるべくサイズを小さくするためビットレートを指定）
        videoclip.audio.write_audiofile(audio_output_path, bitrate="64k", logger=None)
        
        # 明示的に閉じてメモリ・ファイルディスクリプタを解放
        videoclip.close()
        
        return audio_output_path
        
    except Exception as e:
        raise RuntimeError(f"音声抽出エラー: {str(e)}")
