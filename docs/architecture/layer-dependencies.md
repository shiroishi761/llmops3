# レイヤー間の依存関係ルール

## 基本原則

### 1. 依存方向の制約
- **下方向のみ**: 上位層は下位層に依存できるが、逆は禁止
- **ドメイン層の独立性**: ドメイン層は他の層に依存しない
- **循環依存の禁止**: 層間で循環する依存関係は作らない

### 2. インターフェースによる依存性逆転
```
# 良い例：ドメイン層がインターフェースを定義
Domain Layer:
  ├── repositories/
  │   └── experiment_repository.py  # インターフェース定義

Infrastructure Layer:
  ├── repositories/
  │   └── langfuse_experiment_repository.py  # 実装
```

## 各層の依存関係詳細

### インターフェース層
**依存可能**:
- Application層のユースケース
- Application層のDTO
- （直接的には）Infrastructure層の設定

**依存禁止**:
- Domain層のモデル（DTOを経由）
- Infrastructure層の実装詳細

### アプリケーション層
**依存可能**:
- Domain層のモデル
- Domain層のサービス
- Domain層のリポジトリインターフェース

**依存禁止**:
- Interface層
- Infrastructure層の実装詳細（インターフェース経由のみ）

### ドメイン層
**依存可能**:
- なし（完全に独立）

**依存禁止**:
- すべての他層

### インフラストラクチャ層
**依存可能**:
- Domain層のモデル
- Domain層のリポジトリインターフェース
- Application層のユースケース（イベント処理等）

**依存禁止**:
- Interface層

## 実装例

### 良い例：リポジトリパターン
```python
# domain/repositories/experiment_repository.py
from abc import ABC, abstractmethod
from domain.models import Experiment

class ExperimentRepository(ABC):
    @abstractmethod
    async def save(self, experiment: Experiment) -> None:
        pass

# infrastructure/repositories/file_experiment_repository.py
from domain.repositories import ExperimentRepository
from domain.models import Experiment

class FileExperimentRepository(ExperimentRepository):
    async def save(self, experiment: Experiment) -> None:
        # ファイルシステムへの保存実装
        pass
```

### 悪い例：直接依存
```python
# ❌ domain/services/experiment_service.py
import langfuse  # 外部ライブラリへの直接依存

class ExperimentService:
    def __init__(self):
        self.client = langfuse.Client()  # NG
```

## 依存性注入の実践

### 1. コンストラクタ注入
```python
# application/use_cases/run_experiment.py
class RunExperimentUseCase:
    def __init__(
        self,
        experiment_repo: ExperimentRepository,
        llm_service: LLMServiceInterface
    ):
        self.experiment_repo = experiment_repo
        self.llm_service = llm_service
```

### 2. ファクトリーパターン
```python
# infrastructure/factories/use_case_factory.py
class UseCaseFactory:
    @staticmethod
    def create_run_experiment_use_case() -> RunExperimentUseCase:
        repo = FileExperimentRepository()
        llm_service = GeminiLLMService()
        return RunExperimentUseCase(repo, llm_service)
```

## チェックリスト

実装時に確認すべき項目：

- [ ] ドメイン層が他層のコードをimportしていないか
- [ ] インフラ層の実装詳細がドメイン層に漏れていないか
- [ ] 各層間のデータ受け渡しにDTOを使用しているか
- [ ] 依存性注入を適切に使用しているか
- [ ] 循環依存が発生していないか