"""Geminiサービス"""
import time
from typing import Dict, Any, Union, Optional, List
import json
import os

from google import genai
from google.genai import types

from ...application.services.configuration_service import ConfigurationService
from ...application.services.prompt_service import PromptService

class GeminiService:
    """Google Gemini APIとの連携を管理するサービス"""
    
    def __init__(self, config_service: ConfigurationService, name: str = "gemini_service", prompt_service: Optional[PromptService] = None):
        """
        初期化
        
        Args:
            config_service: 設定サービス（必須）
            name: サービス名（デフォルト: "gemini_service"）
            prompt_service: プロンプトサービス（オプション）
        """
        self.config = config_service
        self.name = name
        self.prompt_service = prompt_service
        
        # 環境変数にAPI keyを設定
        os.environ["GOOGLE_API_KEY"] = self.config.gemini_api_key
        
        # 新しいSDKのクライアントを初期化
        self.client = genai.Client()
        
        # デフォルトのモデル設定
        self.default_model = "gemini-1.5-flash"  # 最新のモデルに変更
        self.default_temperature = 0.1
        self.default_max_tokens = 8000  # トークン数を増やす
        
    def extract(
        self,
        prompt: Optional[str] = None,
        prompt_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        include_thinking: Optional[bool] = None,
        thinking_budget: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        プロンプトを使用してデータを抽出
        
        Args:
            prompt: 実行するプロンプト（後方互換性）
            prompt_name: プロンプト名（プロンプトサービスから取得）
            input_data: プロンプトに注入するデータ
            model_name: モデル名（オプション）
            temperature: 温度パラメータ（オプション）
            max_tokens: 最大トークン数（オプション）
            include_thinking: 推論プロセスを含めるか（thinking-expモデル用）
            thinking_budget: 推論に使用するトークン数
                - 0: 推論を無効化
                - -1: 動的推論（モデルが自動判断）
                - 正の数: 具体的なトークン数（例: 1024, 8192）
                - None: モデルのデフォルト値を使用
            
        Returns:
            抽出されたデータ（辞書形式）
        """
        # モデル名を決定
        model = model_name or self.default_model
        
        # 基本設定
        config_dict = {
            "temperature": temperature or self.default_temperature,
            "max_output_tokens": max_tokens or self.default_max_tokens,
        }
        
        # thinking-expモデルの場合、thinking_configを追加
        self.is_thinking_model = "thinking" in model
        self.include_thinking = include_thinking if include_thinking is not None else True
        
        if self.is_thinking_model:
            # thinking_budgetが指定されていない場合のデフォルト値
            if thinking_budget is None:
                if "2.5" in model:
                    thinking_budget = 16384  # 2.5はより深い推論
                elif "2.0" in model:
                    thinking_budget = 8192   # 2.0は標準的な推論
                else:
                    thinking_budget = 4096   # その他
            
            config_dict["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_budget)
        
        # 設定オブジェクトを作成
        config = types.GenerateContentConfig(**config_dict)
        
        # プロンプトの準備
        if prompt:
            # 後方互換性: 直接プロンプトが渡された場合
            final_prompt = prompt
        elif prompt_name and self.prompt_service:
            # プロンプト名からテンプレートを取得
            prompt_template = self.prompt_service.get_prompt(prompt_name)
            
            # input_dataがあれば注入
            if input_data:
                final_prompt = prompt_template
                for key, value in input_data.items():
                    placeholder = f"{{{key}}}"
                    if isinstance(value, str):
                        final_prompt = final_prompt.replace(placeholder, value)
                    else:
                        final_prompt = final_prompt.replace(placeholder, str(value))
            else:
                final_prompt = prompt_template
        else:
            raise ValueError("プロンプトまたはプロンプト名が必要です")
        
        start_time = time.time()
        
        try:
            # コンテンツ生成
            response = self.client.models.generate_content(
                model=model,
                contents=final_prompt,
                config=config
            )
            
            # レスポンステキストを取得
            response_text = response.text
            
            # thinking-expモデルの場合、推論プロセスを抽出
            thinking_content = None
            if self.is_thinking_model:
                # 新しいSDKでの推論プロセスの取得方法を確認
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'thought') and part.thought:
                                thinking_content = part.thought
                                break
                
                # もし取得できない場合は、<thinking>タグから抽出
                if not thinking_content and "<thinking>" in response_text and "</thinking>" in response_text:
                    start_idx = response_text.find("<thinking>") + len("<thinking>")
                    end_idx = response_text.find("</thinking>")
                    thinking_content = response_text[start_idx:end_idx].strip()
                    
                    # 推論プロセスを除外する場合は、<thinking>タグを削除
                    if not self.include_thinking:
                        response_text = response_text[:response_text.find("<thinking>")] + response_text[response_text.find("</thinking>") + len("</thinking>"):]
                        response_text = response_text.strip()
            
            # レスポンスをパース
            result = self._parse_json_response(response_text)
            
            # 実行時間を計算
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # 使用量情報を取得
            usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
            return_data = {
                "data": result,
                "execution_time_ms": execution_time_ms,
                "usage": usage
            }
            
            # 推論プロセスが含まれている場合は追加
            if thinking_content and self.include_thinking:
                return_data["thinking_process"] = thinking_content
            
            return return_data
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract data: {str(e)}")
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        レスポンステキストからJSONを抽出してパース
        
        Args:
            response_text: レスポンステキスト
            
        Returns:
            パースされたJSONデータ
        """
        # レスポンステキストを整形
        text = response_text.strip()
        
        # ```json ブロックを探す
        if "```json" in text:
            # ```json の次の行から ``` までを抽出
            lines = text.split('\n')
            in_json_block = False
            json_lines = []
            
            for line in lines:
                if line.strip() == "```json":
                    in_json_block = True
                    continue
                elif line.strip() == "```" and in_json_block:
                    break
                elif in_json_block:
                    json_lines.append(line)
            
            if json_lines:
                text = '\n'.join(json_lines)
        
        # ``` ブロックを探す（言語指定なし）
        elif text.startswith("```") and text.endswith("```"):
            # 最初と最後の```を除去
            lines = text.split('\n')
            if len(lines) > 2:
                text = '\n'.join(lines[1:-1])
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # JSONの修復を試みる
            import re
            
            # よくあるJSONエラーを修正
            fixed_text = text
            
            # 1. 末尾のカンマを削除
            fixed_text = re.sub(r',(\s*})', r'\1', fixed_text)
            fixed_text = re.sub(r',(\s*\])', r'\1', fixed_text)
            
            # 2. エスケープされていない改行を修正
            # 文字列内の改行を\nに置換（簡易的な処理）
            fixed_text = re.sub(r'("(?:[^"\\]|\\.)*?")', lambda m: m.group(1).replace('\n', '\\n'), fixed_text)
            
            # 3. 不完全な文字列を検出して修正を試みる
            # 最後の未閉じ文字列を探して閉じる
            if '"' in str(e):
                # 最後の開いているクォートを見つけて閉じる
                quote_positions = [i for i, char in enumerate(fixed_text) if char == '"']
                if len(quote_positions) % 2 == 1:
                    # 奇数個のクォートがある場合、最後に閉じクォートを追加
                    fixed_text = fixed_text + '"'
                    # さらに、オブジェクトや配列を適切に閉じる
                    open_braces = fixed_text.count('{') - fixed_text.count('}')
                    open_brackets = fixed_text.count('[') - fixed_text.count(']')
                    fixed_text += ']' * open_brackets + '}' * open_braces
            
            try:
                return json.loads(fixed_text)
            except json.JSONDecodeError as e2:
                # json5ライブラリを試す（より寛容なパーサー）
                try:
                    import json5
                    return json5.loads(text)
                except Exception as e3:
                    # デバッグのために完全なJSONを保存
                    import os
                    debug_file = "/app/debug_json.json"
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(text)
                    # 最終的にダメな場合はエラーを投げる
                    raise RuntimeError(f"Failed to parse JSON: {str(e)}\nDebug file saved to: {debug_file}\nFirst 500 chars: {text[:500]}...")
