"""CLIインターフェース"""
import sys
import argparse
import logging
from pathlib import Path

from .infrastructure.di_container import DIContainer
from .infrastructure.report.html_report_generator import HTMLReportGenerator
import asyncio


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


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
    
    # generate-multi-dataset-report コマンド
    multi_report_parser = subparsers.add_parser(
        "generate-multi-dataset-report",
        help="複数の実験結果から統合HTMLレポートを生成する"
    )
    multi_report_parser.add_argument(
        "--title",
        type=str,
        required=True,
        help="レポートのタイトル"
    )
    multi_report_parser.add_argument(
        "--experiments",
        type=str,
        nargs="+",
        required=True,
        help="実験名のリスト (例: --experiments 実験1 実験2 実験3)"
    )
    multi_report_parser.add_argument(
        "--config",
        type=str,
        default="experiments/experiments.yml",
        help="実験設定ファイルのパス (デフォルト: experiments/experiments.yml)"
    )
    multi_report_parser.add_argument(
        "--output",
        type=str,
        help="出力ファイル名 (指定しない場合は自動生成)"
    )
    multi_report_parser.add_argument(
        "--description",
        type=str,
        help="レポートの説明文"
    )
    
    args = parser.parse_args()
    
    if args.command == "run-experiment":
        asyncio.run(run_experiment(args.config, args.name))
    elif args.command == "generate-report":
        generate_report(args.result_path)
    elif args.command == "generate-multi-dataset-report":
        generate_multi_dataset_report(args.title, args.experiments, args.config, args.output, args.description)
    else:
        parser.print_help()
        sys.exit(1)


async def run_experiment(config_path: str, experiment_name: str):
    """実験を実行"""
    try:
        # パスの検証
        path = Path(config_path)
        if not path.exists():
            logger.error(f"エラー: 実験設定ファイルが見つかりません: {config_path}")
            sys.exit(1)
            
        logger.info(f"実験設定を読み込んでいます: {config_path}")
        logger.info(f"実験名: {experiment_name}")
        logger.info("-" * 50)
        
        # DIコンテナからユースケースを取得
        container = DIContainer()
        use_case = container.create_run_experiment_use_case()
        result = await use_case.execute_from_config_path(config_path, experiment_name)
        
        logger.info("-" * 50)
        logger.info("\n実験結果:")
        logger.info(f"  ステータス: {result.status}")
        logger.info(f"  処理ドキュメント数: {result.summary.total_documents}")
        logger.info(f"  成功: {result.summary.successful_count}")
        logger.info(f"  失敗: {result.summary.failed_count}")
        logger.info(f"  全体精度: {result.summary.overall_accuracy:.2%}")
        
        if hasattr(result.summary, 'field_scores') and result.summary.field_scores:
            logger.info("\n  フィールド別スコア (重み考慮):")
            # スコアの高い順にソート
            sorted_fields = sorted(
                result.summary.field_scores.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )
            for field, info in sorted_fields:
                score = info['score']
                weight = info['weight']
                logger.info(f"    {field}: {score:.2%} (重み: {weight})")
                
        if result.errors:
            logger.warning(f"\n  エラー: {len(result.errors)}件")
            for error in result.errors[:5]:  # 最初の5件のみ表示
                logger.warning(f"    - {error.document_id}: {error.error_message}")
            if len(result.errors) > 5:
                logger.warning(f"    ... 他 {len(result.errors) - 5} 件")
                
        logger.info(f"\n結果ファイル: {result.result_file_path}")
        
        # HTMLレポートを生成するか確認
        print("\nHTMLレポートを生成しますか？ (y/n): ", end="")
        if input().lower() == 'y':
            generate_report(result.result_file_path)
        
    except KeyboardInterrupt:
        logger.warning("\n\n実験が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nエラーが発生しました: {str(e)}")
        sys.exit(1)


def generate_report(result_path: str):
    """実験結果からHTMLレポートを生成"""
    try:
        # パスの検証
        path = Path(result_path)
        if not path.exists():
            logger.error(f"エラー: 結果ファイルが見つかりません: {result_path}")
            sys.exit(1)
        
        logger.info(f"結果ファイルを読み込んでいます: {result_path}")
        
        # レポート生成
        generator = HTMLReportGenerator()
        report_path = generator.generate_from_result_file(result_path)
        
        logger.info(f"HTMLレポートが生成されました: {report_path}")
        logger.info(f"ブラウザでファイルを開いて確認してください。")
        
    except Exception as e:
        logger.error(f"\nレポート生成エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_multi_dataset_report(title: str, experiments: list, config_path: str, output_file: str = None, description: str = None):
    """複数データセットレポートを生成"""
    try:
        logger.info(f"複数データセットレポートを生成しています...")
        logger.info(f"タイトル: {title}")
        logger.info(f"実験数: {len(experiments)}")
        logger.info(f"実験リスト: {', '.join(experiments)}")
        
        # HTMLレポートジェネレーターを使用して直接レポートを生成
        generator = HTMLReportGenerator()
        report_path = generator.generate_multi_dataset_report(title, experiments, output_file, description)
        
        logger.info(f"複数データセットレポートが生成されました: {report_path}")
        logger.info(f"ブラウザでファイルを開いて確認してください。")
        
    except Exception as e:
        logger.error(f"\n複数データセットレポート生成エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()