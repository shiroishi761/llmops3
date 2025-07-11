# ファイルベースリポジトリ実装

## 概要
ローカルファイルシステムを使用したリポジトリ実装。実験結果や抽出結果をJSON形式で保存する。

## FileExperimentRepository

### 責務
- 実験データのファイル保存・読み込み
- ファイル名の管理
- データの整合性確保

### 実装詳細

#### ファイル構造
```
results/
├── experiments/
│   ├── exp_20240115_prompt_v2.json
│   ├── exp_20240116_prompt_v2.json
│   └── index.json  # インデックスファイル
└── summary.json    # 全実験のサマリー
```

#### save
```python
def save(self, experiment: Experiment) -> None:
    # ファイル名の生成
    filename = f"exp_{experiment.executed_at}_{experiment.name}.json"
    
    # データのシリアライズ
    data = self._serialize_experiment(experiment)
    
    # ファイルへの書き込み（アトミック）
    self._write_atomic(filepath, data)
    
    # インデックスの更新
    self._update_index(experiment.id, filename)
```

#### find_by_id
```python
def find_by_id(self, experiment_id: str) -> Optional[Experiment]:
    # インデックスからファイル名を取得
    filename = self._get_filename_from_index(experiment_id)
    
    if not filename:
        return None
    
    # ファイルの読み込み
    data = self._read_file(filename)
    
    # デシリアライズ
    return self._deserialize_experiment(data)
```

#### find_recent
```python
def find_recent(self, limit: int = 10) -> List[Experiment]:
    # ファイル一覧を取得
    files = self._list_experiment_files()
    
    # 更新日時でソート
    sorted_files = sorted(files, key=lambda f: f.mtime, reverse=True)
    
    # 上位N件を読み込み
    experiments = []
    for file in sorted_files[:limit]:
        data = self._read_file(file.path)
        experiments.append(self._deserialize_experiment(data))
    
    return experiments
```

### ファイル形式

#### 実験ファイル
```json
{
    "id": "exp_123",
    "name": "prompt_v2_experiment",
    "status": "completed",
    "created_at": "2024-01-15T10:00:00Z",
    "executed_at": "2024-01-15T10:30:00Z",
    "config": {
        "prompt_name": "ocr_extraction_v2",
        "dataset_name": "invoice_test_v1",
        "endpoint": "extract_v2",
        "parallel_execution": 5
    },
    "summary": {
        "total_documents": 50,
        "successful_count": 48,
        "failed_count": 2,
        "overall_accuracy": 0.92
    },
    "results": [...]
}
```

#### インデックスファイル
```json
{
    "experiments": {
        "exp_123": {
            "filename": "exp_20240115_prompt_v2.json",
            "name": "prompt_v2_experiment",
            "executed_at": "2024-01-15T10:30:00Z"
        }
    },
    "last_updated": "2024-01-15T10:35:00Z"
}
```

### エラーハンドリング
- `FileNotFoundError`: ファイル不在
- `JSONDecodeError`: ファイル破損
- `PermissionError`: アクセス権限エラー
- `DiskFullError`: ディスク容量不足

### アトミック書き込み
```python
def _write_atomic(self, filepath: Path, data: Dict) -> None:
    # 一時ファイルに書き込み
    temp_file = filepath.with_suffix('.tmp')
    
    with open(temp_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # アトミックに移動
    temp_file.replace(filepath)
```

## FileExtractionResultRepository

### 責務
- 抽出結果のファイル保存・読み込み
- 大量データの効率的な管理

### ファイル構造
```
results/
├── extractions/
│   ├── 2024-01/
│   │   ├── doc_001/
│   │   │   ├── v1_20240115_103000.json
│   │   │   └── v2_20240115_143000.json
│   │   └── doc_002/
│   └── 2024-02/
└── index/
    └── by_experiment/
        └── exp_123.json
```

### バッチ保存
```python
def save_batch(self, results: List[ExtractionResult]) -> None:
    # トランザクション開始
    transaction_id = self._begin_transaction()
    
    try:
        for result in results:
            self._save_single(result)
        
        # コミット
        self._commit_transaction(transaction_id)
    except Exception as e:
        # ロールバック
        self._rollback_transaction(transaction_id)
        raise
```

### 検索最適化
```python
def find_by_criteria(self, filter: DocumentFilter) -> List[ExtractionResult]:
    # インデックスを使用した高速検索
    matching_files = self._search_index(filter)
    
    # 必要なファイルのみ読み込み
    results = []
    for file_ref in matching_files:
        data = self._read_file(file_ref.path)
        results.append(self._deserialize_result(data))
    
    return results
```

## 共通機能

### FileStorageService

#### 責務
- ファイルI/O操作の抽象化
- 圧縮・暗号化（オプション）
- バックアップ管理

#### 機能
```python
class FileStorageService:
    def read_json(self, path: Path) -> Dict:
        """JSONファイルの読み込み"""
        
    def write_json(self, path: Path, data: Dict) -> None:
        """JSONファイルの書き込み"""
        
    def list_files(self, 
                   directory: Path, 
                   pattern: str = "*.json") -> List[Path]:
        """ファイル一覧の取得"""
        
    def create_backup(self, path: Path) -> Path:
        """バックアップの作成"""
```

### 設定

#### ストレージ設定
```python
storage_config = {
    "base_path": "/data/llmops/results",
    "max_file_size_mb": 100,
    "compression": {
        "enabled": True,
        "algorithm": "gzip"
    },
    "backup": {
        "enabled": True,
        "retention_days": 30
    }
}
```

## パフォーマンス考慮事項

### インデックス戦略
- 実験ID → ファイルパスのマッピング
- 日付別のディレクトリ分割
- メタデータのキャッシュ

### 大容量データ対策
- ストリーミング読み込み
- ページネーション
- 圧縮保存

### 並行アクセス
- ファイルロックの実装
- 読み取り専用モードのサポート

## 実装時の注意点

### データ整合性
- チェックサムの使用
- バージョニング
- 定期的な整合性チェック

### 災害対策
- 自動バックアップ
- 複数場所への保存
- リカバリ手順の文書化

### セキュリティ
- ファイルアクセス権限
- 機密データの暗号化
- 監査ログ