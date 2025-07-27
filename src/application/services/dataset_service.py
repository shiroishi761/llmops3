"""ローカルデータセット管理サービス"""
import json
import yaml
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
            FileNotFoundError: データセットが見つからない場合
            RuntimeError: ファイル読み込みに失敗した場合
        """
        # 新しいフォルダ構造をチェック
        dataset_dir = self.datasets_dir / dataset_name
        if dataset_dir.exists() and dataset_dir.is_dir():
            return self._load_dataset_from_folder(dataset_dir)
        
        # 従来の単一ファイル形式をチェック（後方互換性のため）
        dataset_file = self.datasets_dir / f"{dataset_name}.json"
        if dataset_file.exists():
            return self._load_dataset_from_file(dataset_file)
        
        raise FileNotFoundError(
            f"データセットが見つかりません: {dataset_name}\n"
            f"以下のいずれかの形式でデータセットを配置してください:\n"
            f"  - フォルダ形式: {dataset_dir}/\n"
            f"  - ファイル形式: {dataset_file}"
        )
    
    def _load_dataset_from_folder(self, dataset_dir: Path) -> List[Dict[str, Any]]:
        """フォルダ構造からデータセットを読み込み"""
        documents = []
        
        try:
            # 各データファイルを読み込み（ファイル名がドキュメントID）
            for data_file in sorted(dataset_dir.glob("*")):
                if not data_file.is_file():
                    continue
                    
                # サポートされる拡張子
                if data_file.suffix not in [".json", ".yml", ".yaml"]:
                    continue
                
                # ファイル名から拡張子を除いてIDとする
                doc_id = data_file.stem
                
                # 数字のみのファイル名を対象とする（例: 000.yml, 001.json）
                if not doc_id.isdigit():
                    continue
                
                # ファイル形式に応じて読み込み
                with open(data_file, "r", encoding="utf-8") as f:
                    if data_file.suffix == ".json":
                        doc_data = json.load(f)
                    else:  # YAML
                        doc_data = yaml.safe_load(f)
                
                # ドキュメントを構築（IDはファイル名から取得）
                documents.append({
                    "id": doc_id,
                    "input": doc_data["input"],
                    "expected_output": doc_data["expected_output"]
                })
            
            return documents
            
        except Exception as e:
            raise RuntimeError(f"データセットフォルダの読み込みに失敗しました: {dataset_dir}, {str(e)}")
    
    def _load_dataset_from_file(self, dataset_file: Path) -> List[Dict[str, Any]]:
        """単一ファイルからデータセットを読み込み（後方互換性）"""
        try:
            with open(dataset_file, "r", encoding="utf-8") as f:
                dataset_data = json.load(f)
            
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
            データセット名のリスト
        """
        if not self.datasets_dir.exists():
            return []
        
        datasets = []
        
        # フォルダ形式のデータセットを検索
        for item in self.datasets_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 数字のデータファイル（JSON/YAML）があるかチェック
                if any(item.glob("[0-9]*.[jy][sa]?[om][nl]?")):
                    datasets.append(item.name)
        
        # ファイル形式のデータセットを検索（後方互換性）
        for data_file in self.datasets_dir.glob("*"):
            if data_file.is_file() and data_file.suffix in [".json", ".yml", ".yaml"]:
                if not data_file.stem.endswith('_backup'):
                    datasets.append(data_file.stem)
        
        return sorted(list(set(datasets)))
    
    def dataset_exists(self, dataset_name: str) -> bool:
        """
        データセットが存在するかチェック
        
        Args:
            dataset_name: データセット名
            
        Returns:
            存在するかどうか
        """
        # フォルダ形式をチェック
        dataset_dir = self.datasets_dir / dataset_name
        if dataset_dir.exists() and dataset_dir.is_dir():
            return True
        
        # ファイル形式をチェック（後方互換性）
        dataset_file = self.datasets_dir / f"{dataset_name}.json"
        return dataset_file.exists()
