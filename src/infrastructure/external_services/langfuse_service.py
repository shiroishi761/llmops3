"""Langfuseサービス"""
from typing import List, Dict, Any, Optional
from langfuse import Langfuse

from ..config.configuration_service import ConfigurationService


class LangfuseService:
    """Langfuseとの連携を管理するサービス"""
    
    def __init__(self, config_service: Optional[ConfigurationService] = None):
        """
        初期化
        
        Args:
            config_service: 設定サービス
        """
        self.config = config_service or ConfigurationService()
        
        # Langfuseクライアントを初期化
        self.client = Langfuse(
            public_key=self.config.langfuse_public_key,
            secret_key=self.config.langfuse_secret_key,
            host=self.config.langfuse_host
        )
        
    def get_prompt(self, prompt_name: str) -> str:
        """
        プロンプトテンプレートを取得
        
        Args:
            prompt_name: プロンプト名
            
        Returns:
            プロンプトテンプレート文字列
        """
        try:
            prompt = self.client.get_prompt(prompt_name)
            return prompt.compile()
        except Exception as e:
            raise RuntimeError(f"Failed to get prompt '{prompt_name}': {str(e)}")
    
    def get_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        """
        データセットを取得
        
        Args:
            dataset_name: データセット名
            
        Returns:
            データセットアイテムのリスト
        """
        try:
            dataset = self.client.get_dataset(dataset_name)
            items = []
            
            # データセットのアイテムを取得
            for item in dataset.items:
                items.append({
                    "id": item.id,
                    "input": item.input,
                    "expected_output": item.expected_output or {}
                })
                
            return items
        except Exception as e:
            raise RuntimeError(f"Failed to get dataset '{dataset_name}': {str(e)}")
    
    def create_trace(self, experiment_name: str, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """
        トレースを作成
        
        Args:
            experiment_name: 実験名
            metadata: メタデータ
            
        Returns:
            トレースオブジェクト
        """
        return self.client.trace(
            name=experiment_name,
            metadata=metadata or {}
        )
    
    def create_generation(
        self,
        trace_id: str,
        name: str,
        prompt: str,
        completion: str,
        model: str,
        usage: Optional[Dict[str, int]] = None
    ) -> None:
        """
        生成ログを作成
        
        Args:
            trace_id: トレースID
            name: 生成の名前
            prompt: プロンプト
            completion: 完了したテキスト
            model: モデル名
            usage: 使用量情報
        """
        self.client.generation(
            trace_id=trace_id,
            name=name,
            input=prompt,
            output=completion,
            model=model,
            usage=usage
        )
    
    def score_trace(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None
    ) -> None:
        """
        トレースにスコアを付ける
        
        Args:
            trace_id: トレースID
            name: スコア名
            value: スコア値
            comment: コメント
        """
        self.client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment
        )
    
    def flush(self) -> None:
        """バッファをフラッシュ"""
        self.client.flush()
    
    def update_dataset_item(
        self,
        dataset_name: str,
        item_id: str,
        input_data: Dict[str, Any],
        expected_output: Dict[str, Any]
    ) -> None:
        """
        データセットアイテムを更新
        
        Args:
            dataset_name: データセット名
            item_id: アイテムID
            input_data: 入力データ
            expected_output: 期待される出力
        """
        try:
            # アイテムを更新
            self.client.create_dataset_item(
                dataset_name=dataset_name,
                input=input_data,
                expected_output=expected_output,
                id=item_id
            )
        except Exception as e:
            raise RuntimeError(f"Failed to update dataset item '{item_id}' in dataset '{dataset_name}': {str(e)}")