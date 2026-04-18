import streamlit as st
import os
import tempfile
from dotenv import load_dotenv

from audio_processor import extract_audio_from_video
from gemini_processor import process_audio_with_gemini

# .envの読み込み（ローカル実行用）
load_dotenv()

st.set_page_config(page_title="動画解析アプリ(Gemini版)", page_icon="✨", layout="centered")

st.title("✨ 動画文字起こし・要約アプリ (Gemini版)")
st.write("動画ファイルをアップロードすると、Googleの無料のGemini AIが「文字起こし」「要約」「やることリスト（期間込み）」を一度に抽出し、Markdownファイルとして出力します。")
st.info("APIキーをお持ちでない場合は、[Google AI Studio](https://aistudio.google.com/) から **無料** で取得できます。")

# Google APIキーの取得
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Gemini APIキーを入力してください:", type="password")

if api_key:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    try:
        import re
        # APIキーを使って利用可能なモデル一覧を動的に取得
        raw_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # モデル名に含まれるバージョン番号(例: 1.5, 2.5)を大きい順に並び替え（最新を上へ）
        def _get_version(name):
            match = re.search(r'gemini-(\d+\.\d+)', name)
            return float(match.group(1)) if match else 0.0
            
        models = sorted(raw_models, key=_get_version, reverse=True)
        
        # デフォルトを選択
        default_idx = next((i for i, m in enumerate(models) if "gemini-2.5-flash" == m or "gemini-2.5-flash" in m), 0)
        selected_model = st.selectbox("✨ 使用するAIモデルを選択してください", models, index=default_idx)
    except Exception as e:
        st.warning("モデル一覧の取得に失敗しました。APIキーが正しいか確認してください。")
        selected_model = "gemini-2.5-flash"
else:
    selected_model = "gemini-2.5-flash"
    st.info("APIキーを入力すると、利用できる最新モデルの一覧から選択可能になります。")

uploaded_file = st.file_uploader("動画ファイルをアップロードしてください (mp4, mov, mkv等)", type=["mp4", "mov", "avi", "mkv", "webm"])

if uploaded_file is not None and api_key:
    if st.button("処理開始", type="primary"):
        with st.status("動画を処理中...", expanded=True) as status:
            temp_video_path = None
            audio_path = None
            try:
                # 1. 一時ファイルとして動画を保存
                st.write("📥 動画ファイルをローカルに保存中...")
                temp_dir = tempfile.gettempdir()
                temp_video_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(temp_video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 2. 音声抽出 (MoviePy)
                st.write("🎵 動画から音声トラックを抽出中...")
                audio_path = extract_audio_from_video(temp_video_path)
                
                # 3. Geminiでの一括処理
                st.write(f"✨ Gemini AI ({selected_model}) で「文字起こし・要約・やることリスト」を同時抽出中...")
                st.write("（※音声の長さにより数十秒〜1分ほど待機します）")
                extracted = process_audio_with_gemini(audio_path, api_key, model_name=selected_model)
                
                status.update(label="処理が完了しました！", state="complete", expanded=False)
                
                st.success("全ての処理が完了しました。以下の結果を確認のうえ、ダウンロードしてください。")
                
                # 結果の表示
                st.header("📌 要約")
                st.write(extracted["summary"])
                
                st.header("📝 やることリスト")
                st.write(extracted["tasks"])
                
                with st.expander("全文の文字起こしを開く"):
                    st.text_area("本文", extracted["transcript"], height=300)
                    
                # Markdown用テキストの構築
                markdown_content = f"""# 動画処理結果レポート (Gemini)

## 📌 要約
{extracted['summary']}

## 📝 やることリスト
{extracted['tasks']}

---

## 📄 全文の文字起こし
{extracted['transcript']}
"""
                st.download_button(
                    label="Markdownファイル(.md)をダウンロード",
                    data=markdown_content,
                    file_name="gemini_transcription.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                status.update(label="エラーが発生しました", state="error", expanded=False)
                st.error(f"エラー: {str(e)}")
            finally:
                # クリーンアップ処理
                try:
                    if temp_video_path and os.path.exists(temp_video_path):
                        os.remove(temp_video_path)
                    if audio_path and os.path.exists(audio_path):
                        os.remove(audio_path)
                except:
                    pass

elif uploaded_file is not None and not api_key:
    st.warning("処理を開始するには、Gemini APIキーを入力してください。")
