"""ローカルデータセット管理サービス"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class DatasetService:
    """ローカルファイルベースのデータセット管理サービス"""
    
    def __init__(self, datasets_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            datasets_dir: データセットディレクトリのパス（デフォルト: プロジェクトルート/datasets）
        """
        if datasets_dir:
            self.datasets_dir = Path(datasets_dir)
        else:
            # プロジェクトルートからdatasetsディレクトリを設定
            project_root = Path(__file__).parent.parent.parent.parent
            self.datasets_dir = project_root / "datasets"
    
    def get_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        """
        データセットを取得
        
        Args:
            dataset_name: データセット名
            
        Returns:
            データセットドキュメントのリスト
            
        Raises:
            FileNotFoundError: データセットファイルが見つからない場合
            RuntimeError: ファイル読み込みに失敗した場合
        """
        # ファイルパスを構築
        dataset_file = self.datasets_dir / f"{dataset_name}.json"
        
        if not dataset_file.exists():
            raise FileNotFoundError(
                f"データセットファイルが見つかりません: {dataset_file}\n"
                f"datasets/フォルダに {dataset_name}.json ファイルを配置してください"
            )
        
        try:
            # ファイルを読み込み
            with open(dataset_file, "r", encoding="utf-8") as f:
                dataset_data = json.load(f)
            
            # Langfuseと同じ形式に変換
            documents = []
            for document_data in dataset_data:
                documents.append({
                    "id": document_data["id"],
                    "input": document_data["input"],
                    "expected_output": document_data.get("expected_output", {})
                })
            
            return documents
            
        except Exception as e:
            raise RuntimeError(f"データセットファイルの読み込みに失敗しました: {dataset_file}, {str(e)}")
    
    def list_available_datasets(self) -> List[str]:
        """
        利用可能なデータセット名の一覧を取得
        
        Returns:
            データセット名のリスト（拡張子なし）
        """
        if not self.datasets_dir.exists():
            return []
        
        dataset_files = list(self.datasets_dir.glob("*.json"))
        return [f.stem for f in dataset_files]
    
    def dataset_exists(self, dataset_name: str) -> bool:
        """
        データセットファイルが存在するかチェック
        
        Args:
            dataset_name: データセット名
            
        Returns:
            存在するかどうか
        """
        dataset_file = self.datasets_dir / f"{dataset_name}.json"
        return dataset_file.exists()