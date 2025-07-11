.PHONY: help build up down logs shell test run-experiment clean

help:
	@echo "利用可能なコマンド:"
	@echo "  make build          - Dockerイメージをビルド"
	@echo "  make up             - 開発サーバーを起動"
	@echo "  make down           - コンテナを停止"
	@echo "  make logs           - ログを表示"
	@echo "  make shell          - コンテナ内でbashを起動"
	@echo "  make test           - テストを実行"
	@echo "  make run-experiment - 実験を実行（FILE=experiments/xxx.yml）"
	@echo "  make clean          - キャッシュをクリーンアップ"

build:
	docker-compose build

up:
	docker-compose up

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec app bash

test:
	docker-compose run --rm app pytest

run-experiment:
	@if [ -z "$(FILE)" ]; then \
		echo "エラー: FILE パラメータが必要です"; \
		echo "使用例: make run-experiment FILE=experiments/invoice_test.yml"; \
		exit 1; \
	fi
	docker-compose run --rm cli python -m src.cli run-experiment $(FILE)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete