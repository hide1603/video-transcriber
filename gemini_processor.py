import os
import time
import google.generativeai as genai

def process_audio_with_gemini(audio_path: str, gemini_api_key: str, model_name: str = "gemini-2.5-flash") -> dict:
    """
    Geminiモデルを使用して、音声ファイルから文字起こし・要約・やることリストを一括で抽出する。
    """
    if not gemini_api_key:
        raise ValueError("Google AI Studio (Gemini) APIキーが設定されていません。")
        
    genai.configure(api_key=gemini_api_key)
    
    # 1. 音声ファイルをGeminiのFile APIにアップロード
    myfile = genai.upload_file(audio_path)
    
    # ファイルが処理可能になるまで待機
    while myfile.state.name == 'PROCESSING':
        time.sleep(2)
        myfile = genai.get_file(myfile.name)
        
    if myfile.state.name == 'FAILED':
        raise RuntimeError("音声ファイルのアップロード・処理に失敗しました。")
    
    # 2. プロンプトを作成して生成
    system_instruction = """
あなたは優秀なアシスタントです。提供された音声ファイルから、以下の3点を作成してください。
1. 全体の要約（箇条書きなどを活用して分かりやすく200〜400文字程度）
2. やることリスト（音声内で「〜日までに」などの期限や期間が言及されていればそれも含めてMarkdownのリスト形式で出力。なければ「特になし」とする）
3. 全文の文字起こし（発言の区切りや段落ごとに `[00:00]` のようなタイムライン・タイムスタンプを付与し、必ず行を分けて改行して読みやすくしてください）

出力は必ず以下のフォーマットに従ってください。余計な文字列は含めないでください。

###要約###
（ここに要約）

###やることリスト###
（ここにやることリスト）

###全文の文字起こし###
（ここにタイムラインごとの全文の文字起こし。例：
[00:00] 本日はお集まりいただき...
[00:12] まずはじめに議題ですが...
）
"""
    
    model = genai.GenerativeModel(model_name)
    
    try:
        response = model.generate_content([system_instruction, myfile])
        content = response.text
        
        # 簡易パース
        summary_text = ""
        tasks_text = ""
        transcript_text = ""
        
        try:
            parts = content.split("###やることリスト###")
            summary_text = parts[0].replace("###要約###", "").strip()
            
            if "###全文の文字起こし###" in parts[1]:
                tasks_parts = parts[1].split("###全文の文字起こし###")
                tasks_text = tasks_parts[0].strip()
                transcript_text = tasks_parts[1].strip()
            else:
                tasks_text = parts[1].strip()
                transcript_text = "文字起こしが抽出できませんでした。"
        except Exception:
            # パースに失敗した場合は全体を要約部分に入れる
            summary_text = content
            tasks_text = "フォーマットの解析に失敗しました。要約欄に全体を表示しています。"
            transcript_text = "抽出エラー"
            
        return {
            "summary": summary_text,
            "tasks": tasks_text,
            "transcript": transcript_text
        }
    except Exception as e:
        raise RuntimeError(f"Gemini APIでの処理中にエラーが発生しました: {str(e)}")
    finally:
        # リソースをすぐに削除してクリーンアップ
        genai.delete_file(myfile.name)
