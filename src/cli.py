"""CLIインターフェース"""
import sys
import argparse
import asyncio
import logging
from pathlib import Path

from .application.use_cases.run_experiment import RunExperimentUseCase
from .application.services.configuration_service import ConfigurationService
from .application.services.prompt_service import PromptService
from .application.services.dataset_service import DatasetService
from .infrastructure.external_services.llm_client import LLMClient
from .infrastructure.repositories.file_experiment_repository import FileExperimentRepository
from .domain.services.accuracy_evaluation_service import AccuracyEvaluationService
from .domain.services.items_matching_service import ItemsMatchingService
from .infrastructure.external_services.gemini_service import GeminiService
from .infrastructure.report.html_report_generator import HTMLReportGenerator


def setup_logging():
    """ログ設定を初期化"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="LLMOps精度検証プラットフォーム CLI"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")
    
    # run-experiment コマンド
    run_parser = subparsers.add_parser(
        "run-experiment",
        help="実験を実行する"
    )
    run_parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="実験名 (experiments.ymlで定義された実験名)"
    )
    run_parser.add_argument(
        "--config",
        type=str,
        default="experiments/experiments.yml",
        help="実験設定ファイルのパス (デフォルト: experiments/experiments.yml)"
    )
    
    # generate-report コマンド
    report_parser = subparsers.add_parser(
        "generate-report",
        help="実験結果からHTMLレポートを生成する"
    )
    report_parser.add_argument(
        "result_path",
        type=str,
        help="実験結果ファイルのパス (例: results/experiment_20240115_143052.json)"
    )
    
    
    args = parser.parse_args()
    
    # ログ設定を初期化
    setup_logging()
    
    if args.command == "run-experiment":
        asyncio.run(run_experiment(args.config, args.name))
    elif args.command == "generate-report":
        generate_report(args.result_path)
    else:
        parser.print_help()
        sys.exit(1)


async def run_experiment(config_path: str, experiment_name: str):
    """実験を実行"""
    try:
        # パスの検証
        path = Path(config_path)
        if not path.exists():
            logging.error(f"実験設定ファイルが見つかりません: {config_path}")
            print(f"エラー: 実験設定ファイルが見つかりません: {config_path}")
            sys.exit(1)
            
        logging.info(f"実験設定を読み込んでいます: {config_path}")
        logging.info(f"実験名: {experiment_name}")
        print(f"実験設定を読み込んでいます: {config_path}")
        print(f"実験名: {experiment_name}")
        print("-" * 50)
        
        # 依存関係を直接注入
        config_service = ConfigurationService(field_weights_config_path="config/config.yml")
        prompt_service = PromptService()
        dataset_service = DatasetService()
        llm_client = LLMClient()
        experiment_repository = FileExperimentRepository()
        accuracy_service = AccuracyEvaluationService()
        gemini_service = GeminiService(config_service)
        items_matching_service = ItemsMatchingService(gemini_service)
        
        use_case = RunExperimentUseCase(
            config_service=config_service,
            prompt_service=prompt_service,
            dataset_service=dataset_service,
            llm_client=llm_client,
            experiment_repository=experiment_repository,
            accuracy_service=accuracy_service,
            items_matching_service=items_matching_service
        )
        result = await use_case.execute(config_path, experiment_name)
        
        print("-" * 50)
        print("\n実験結果:")
        print(f"  ステータス: {result.status}")
        print(f"  処理ドキュメント数: {result.summary.total_documents}")
        print(f"  成功: {result.summary.successful_count}")
        print(f"  失敗: {result.summary.failed_count}")
        print(f"  全体精度: {result.summary.overall_accuracy:.2%}")
        
        if hasattr(result.summary, 'field_scores') and result.summary.field_scores:
            print("\n  フィールド別スコア (重み考慮):")
            # スコアの高い順にソート
            sorted_fields = sorted(
                result.summary.field_scores.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )
            for field, info in sorted_fields:
                score = info['score']
                weight = info['weight']
                print(f"    {field}: {score:.2%} (重み: {weight})")
                
        if result.errors:
            print(f"\n  エラー: {len(result.errors)}件")
            for error in result.errors[:5]:  # 最初の5件のみ表示
                print(f"    - {error.document_id}: {error.error_message}")
            if len(result.errors) > 5:
                print(f"    ... 他 {len(result.errors) - 5} 件")
                
        print(f"\n結果ファイル: {result.result_file_path}")
        
        # HTMLレポートを生成するか確認
        print("\nHTMLレポートを生成しますか？ (y/n): ", end="")
        if input().lower() == 'y':
            generate_report(result.result_file_path)
        
    except KeyboardInterrupt:
        print("\n\n実験が中断されました")
        sys.exit(1)
    except Exception as e:
        logging.error(f"エラーが発生しました: {str(e)}")
        print(f"\nエラーが発生しました: {str(e)}")
        sys.exit(1)


def generate_report(result_path: str):
    """実験結果からHTMLレポートを生成"""
    try:
        # パスの検証
        path = Path(result_path)
        if not path.exists():
            logging.error(f"結果ファイルが見つかりません: {result_path}")
            print(f"エラー: 結果ファイルが見つかりません: {result_path}")
            sys.exit(1)
        
        logging.info(f"結果ファイルを読み込んでいます: {result_path}")
        
        # レポート生成
        generator = HTMLReportGenerator()
        report_path = generator.generate_from_result_file(result_path)
        
        print(f"HTMLレポートが生成されました: {report_path}")
        print(f"ブラウザでファイルを開いて確認してください。")
        
    except Exception as e:
        logging.error(f"レポート生成エラー: {str(e)}")
        print(f"\nレポート生成エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




if __name__ == "__main__":
    main()