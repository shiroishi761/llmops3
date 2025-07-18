"""HTMLレポート生成サービス"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Template
import json

from .html_template import HTML_TEMPLATE, MULTI_DATASET_TEMPLATE


class HTMLReportGenerator:
    """実験結果のHTMLレポートを生成するサービス"""
    
    def __init__(self, output_dir: Path = Path("reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.template = Template(HTML_TEMPLATE)
        self.multi_dataset_template = Template(MULTI_DATASET_TEMPLATE)
    
    def generate_from_result_file(self, result_file_path: str) -> str:
        """結果ファイルからHTMLレポートを生成"""
        with open(result_file_path, 'r', encoding='utf-8') as f:
            experiment_data = json.load(f)
        
        return self.generate(experiment_data)
    
    def generate(self, experiment_data: Dict[str, Any]) -> str:
        """実験データからHTMLレポートを生成"""
        # レポートのコンテキストデータを準備
        context = self._prepare_context(experiment_data)
        
        # HTMLを生成
        html_content = self.template.render(**context)
        
        # ファイル名を生成
        experiment_name = experiment_data.get('name', 'experiment')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self._sanitize_filename(experiment_name)}_{timestamp}.html"
        output_path = self.output_dir / filename
        
        # HTMLファイルを保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _prepare_context(self, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """テンプレート用のコンテキストデータを準備"""
        summary = experiment_data.get('summary', {})
        
        # 結果データを処理
        results = []
        for result in experiment_data.get('results', []):
            # itemsフィールドの特別な処理
            processed_result = result.copy()
            
            # expected_dataとextracted_dataのitemsを適切に処理
            if 'expected_data' in processed_result:
                expected_items = self._parse_items(processed_result['expected_data'].get('items'))
                processed_result['expected_data']['items'] = expected_items
            
            if 'extracted_data' in processed_result:
                extracted_items = self._parse_items(processed_result['extracted_data'].get('items'))
                processed_result['extracted_data']['items'] = extracted_items
            
            # 精度をフォーマット
            if 'accuracy' in processed_result:
                processed_result['accuracy_formatted'] = "{:.1f}".format(processed_result['accuracy'] * 100)
            
            # field_resultsを処理して、フィールドを固定順序で並べ替える
            if 'field_results' in processed_result:
                # フィールドの表示順序を定義（itemsは最後）
                field_order = [
                    'doc_type', 'doc_title', 'doc_number', 'doc_date', 'doc_transaction',
                    'destination', 'destination_customer_id',
                    'issuer', 'issuer_customer_id', 'issuer_address', 'issuer_zip', 'issuer_phone_number',
                    'construction_name', 'construction_site', 'construction_period',
                    'payment_terms', 'expiration_date',
                    'sub_total', 'tax_type', 'tax_price', 'total_price', 't_number',
                    'items'  # itemsは最後
                ]
                
                # 順序に従って並べ替え（辞書化は行わない）
                sorted_metrics = []
                
                # まず、field_orderに含まれるフィールドを順序通りに追加
                for field in field_order:
                    for metric in processed_result['field_results']:
                        if metric.get('field_name') == field:
                            sorted_metrics.append(metric)
                
                # field_orderに含まれていないフィールドも追加（items.*フィールドは含める）
                for metric in processed_result['field_results']:
                    field_name = metric.get('field_name', '')
                    if field_name not in field_order and field_name != 'items':
                        sorted_metrics.append(metric)
                
                processed_result['field_results'] = sorted_metrics
            
            results.append(processed_result)
        
        # 日時のフォーマット
        created_at = self._format_datetime(experiment_data.get('created_at'))
        completed_at = self._format_datetime(experiment_data.get('completed_at'))
        
        # 全体精度をフォーマット
        overall_accuracy = summary.get('overall_accuracy', 0)
        overall_accuracy_formatted = "{:.1f}".format(overall_accuracy * 100)
        
        # 全体スコアを計算
        overall_score = 0.0
        max_possible_score = 0.0
        
        if 'field_scores' in summary and summary['field_scores']:
            total_score = 0.0
            for field, scores in summary['field_scores'].items():
                weight = scores.get('weight', 0.0)
                score = scores.get('score', 0.0)
                # 現在のスコア: 重み × 一致度（0〜1）
                total_score += weight * score
                # 最大可能スコア: 重みの合計
                max_possible_score += weight
                
            overall_score = total_score
        else:
            # field_scoresがない場合は、精度を使用
            overall_score = overall_accuracy * 100
            max_possible_score = 100
        
        # フィールド精度をフォーマット
        field_accuracies = {}
        field_accuracies_formatted = {}
        for field, accuracy in summary.get('field_accuracies', {}).items():
            field_accuracies[field] = accuracy
            field_accuracies_formatted[field] = "{:.1f}".format(accuracy * 100)
        
        return {
            'experiment_name': experiment_data.get('name', '無題の実験'),
            'prompt_name': experiment_data.get('prompt_name', '-'),
            'dataset_name': experiment_data.get('dataset_name', '-'),
            'llm_endpoint': experiment_data.get('llm_endpoint', '-'),
            'created_at': created_at,
            'completed_at': completed_at,
            'overall_accuracy': overall_accuracy,
            'overall_accuracy_formatted': overall_accuracy_formatted,
            'overall_score': overall_score,
            'max_possible_score': max_possible_score,
            'total_documents': summary.get('total_documents', 0),
            'successful_count': summary.get('successful_count', 0),
            'failed_count': summary.get('failed_count', 0),
            'field_accuracies': field_accuracies,
            'field_accuracies_formatted': field_accuracies_formatted,
            'results': results,
            'report_generated_at': datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        }
    
    def _parse_items(self, items_data: Any) -> Optional[list]:
        """itemsフィールドのデータをパース"""
        if items_data is None:
            return None
        
        # 既にリストの場合は処理して返す
        if isinstance(items_data, list):
            return self._format_items(items_data)
        
        # JSON文字列の場合はパース
        if isinstance(items_data, str):
            try:
                parsed = json.loads(items_data)
                if isinstance(parsed, list):
                    return self._format_items(parsed)
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _format_items(self, items: list) -> list:
        """itemsのデータをフォーマット"""
        formatted_items = []
        for item in items:
            formatted_item = item.copy() if isinstance(item, dict) else {}
            
            # 価格と小計を事前にフォーマット
            if 'price' in formatted_item and formatted_item['price'] is not None:
                formatted_item['price_formatted'] = "{:,}".format(int(formatted_item['price']))
            else:
                formatted_item['price_formatted'] = "-"
            
            if 'sub_total' in formatted_item and formatted_item['sub_total'] is not None:
                formatted_item['sub_total_formatted'] = "{:,}".format(int(formatted_item['sub_total']))
            else:
                formatted_item['sub_total_formatted'] = "-"
            
            formatted_items.append(formatted_item)
        
        return formatted_items
    
    def _format_datetime(self, dt_str: Optional[str]) -> str:
        """日時文字列を読みやすい形式にフォーマット"""
        if not dt_str:
            return '-'
        
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime('%Y年%m月%d日 %H:%M:%S')
        except:
            return dt_str
    
    def _sanitize_filename(self, name: str) -> str:
        """ファイル名として使用できる文字列に変換"""
        # ファイル名に使えない文字を置換
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # 長すぎる場合は切り詰める
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        return sanitized
    
    def generate_multi_dataset_report(self, report_title: str, experiment_names: list, output_file_name: Optional[str] = None, description: Optional[str] = None) -> str:
        """複数データセット対応のHTMLレポートを生成"""
        # 実験結果を収集
        experiments = self._collect_experiment_results(experiment_names)
        
        # 全体サマリーを計算
        overall_summary = self._calculate_overall_summary(experiments)
        
        # レポートのコンテキストデータを準備
        context = self._prepare_multi_dataset_context(report_title, experiments, overall_summary, description)
        
        # HTMLを生成
        html_content = self.multi_dataset_template.render(**context)
        
        # ファイル名を生成
        if output_file_name:
            filename = output_file_name
        else:
            sanitized_title = self._sanitize_filename(report_title)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{sanitized_title}_{timestamp}.html"
        
        output_path = self.output_dir / filename
        
        # HTMLファイルを保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _collect_experiment_results(self, experiment_names: list) -> list:
        """実験結果を収集"""
        experiments = []
        
        for experiment_name in experiment_names:
            # 最新の実験結果ファイルを取得
            result_files = self._find_experiment_result_files(experiment_name)
            
            if not result_files:
                continue
                
            # 最新のファイルを読み込み
            latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
            
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    experiment_data = json.load(f)
                
                experiments.append(experiment_data)
                
            except Exception as e:
                continue
        
        return experiments
    
    def _find_experiment_result_files(self, experiment_name: str) -> list:
        """実験結果ファイルを検索"""
        results_dir = Path("results")
        if not results_dir.exists():
            return []
        
        # 実験名でファイルを検索
        result_files = []
        for file_path in results_dir.glob("*.json"):
            if experiment_name in file_path.name:
                result_files.append(file_path)
        
        return result_files
    
    def _calculate_overall_summary(self, experiments: list) -> dict:
        """全体サマリーを計算"""
        if not experiments:
            return {
                'total_experiments': 0,
                'total_documents': 0,
                'total_successful': 0,
                'total_failed': 0,
                'overall_accuracy': 0.0,
                'field_accuracies': {},
                'dataset_summary': {}
            }
        
        total_documents = sum(exp.get('summary', {}).get('total_documents', 0) for exp in experiments)
        total_successful = sum(exp.get('summary', {}).get('successful_count', 0) for exp in experiments)
        total_failed = sum(exp.get('summary', {}).get('failed_count', 0) for exp in experiments)
        
        # 全体精度を計算（重み付き平均）
        total_accuracy_sum = 0.0
        total_weight = 0
        
        for exp in experiments:
            summary = exp.get('summary', {})
            successful_count = summary.get('successful_count', 0)
            if successful_count > 0:
                weight = successful_count
                total_accuracy_sum += summary.get('overall_accuracy', 0.0) * weight
                total_weight += weight
        
        overall_accuracy = total_accuracy_sum / total_weight if total_weight > 0 else 0.0
        
        # フィールド別精度を統合
        field_accuracies = self._aggregate_field_accuracies(experiments)
        
        # データセット別サマリー
        dataset_summary = self._create_dataset_summary(experiments)
        
        return {
            'total_experiments': len(experiments),
            'total_documents': total_documents,
            'total_successful': total_successful,
            'total_failed': total_failed,
            'overall_accuracy': overall_accuracy,
            'field_accuracies': field_accuracies,
            'dataset_summary': dataset_summary
        }
    
    def _aggregate_field_accuracies(self, experiments: list) -> dict:
        """フィールド別精度を統合"""
        field_stats = {}
        
        for exp in experiments:
            summary = exp.get('summary', {})
            successful_count = summary.get('successful_count', 0)
            if successful_count == 0:
                continue
                
            weight = successful_count
            
            for field_name, accuracy in summary.get('field_accuracies', {}).items():
                if field_name not in field_stats:
                    field_stats[field_name] = {'total_weighted_accuracy': 0.0, 'total_weight': 0}
                
                field_stats[field_name]['total_weighted_accuracy'] += accuracy * weight
                field_stats[field_name]['total_weight'] += weight
        
        # 重み付き平均を計算
        field_accuracies = {}
        for field_name, stats in field_stats.items():
            if stats['total_weight'] > 0:
                field_accuracies[field_name] = stats['total_weighted_accuracy'] / stats['total_weight']
            else:
                field_accuracies[field_name] = 0.0
        
        return field_accuracies
    
    def _create_dataset_summary(self, experiments: list) -> dict:
        """データセット別サマリーを作成"""
        dataset_groups = {}
        
        for exp in experiments:
            dataset_name = exp.get('dataset_name', '-')
            if dataset_name not in dataset_groups:
                dataset_groups[dataset_name] = []
            dataset_groups[dataset_name].append(exp)
        
        dataset_summary = {}
        for dataset_name, exps in dataset_groups.items():
            total_docs = sum(exp.get('summary', {}).get('total_documents', 0) for exp in exps)
            total_successful = sum(exp.get('summary', {}).get('successful_count', 0) for exp in exps)
            
            # データセット内の平均精度
            if total_successful > 0:
                accuracy_sum = sum(exp.get('summary', {}).get('overall_accuracy', 0.0) * exp.get('summary', {}).get('successful_count', 0) for exp in exps)
                avg_accuracy = accuracy_sum / total_successful
            else:
                avg_accuracy = 0.0
            
            dataset_summary[dataset_name] = {
                'experiment_count': len(exps),
                'total_documents': total_docs,
                'total_successful': total_successful,
                'average_accuracy': avg_accuracy
            }
        
        return dataset_summary
    
    def _prepare_multi_dataset_context(self, report_title: str, experiments: list, overall_summary: dict, description: Optional[str] = None) -> Dict[str, Any]:
        """複数データセットレポート用のコンテキストデータを準備"""
        # 実験結果を整理
        formatted_experiments = []
        for exp in experiments:
            summary = exp.get('summary', {})
            experiment_data = {
                'name': exp.get('name', '無題の実験'),
                'dataset_name': exp.get('dataset_name', '-'),
                'llm_endpoint': exp.get('llm_endpoint', '-'),
                'prompt_name': exp.get('prompt_name', '-'),
                'status': exp.get('status', 'unknown'),
                'total_documents': summary.get('total_documents', 0),
                'successful_count': summary.get('successful_count', 0),
                'failed_count': summary.get('failed_count', 0),
                'overall_accuracy': summary.get('overall_accuracy', 0.0),
                'overall_accuracy_formatted': "{:.1f}".format(summary.get('overall_accuracy', 0.0) * 100),
                'field_accuracies': summary.get('field_accuracies', {}),
                'field_accuracies_formatted': {
                    field: "{:.1f}".format(accuracy * 100) 
                    for field, accuracy in summary.get('field_accuracies', {}).items()
                },
                'created_at': self._format_datetime(exp.get('created_at')),
                'completed_at': self._format_datetime(exp.get('completed_at')),
                'description': exp.get('description')
            }
            formatted_experiments.append(experiment_data)
        
        # 全体サマリーを整理
        total_experiments = overall_summary.get('total_experiments', 0)
        total_documents = overall_summary.get('total_documents', 0)
        total_successful = overall_summary.get('total_successful', 0)
        total_failed = overall_summary.get('total_failed', 0)
        overall_accuracy = overall_summary.get('overall_accuracy', 0.0)
        
        # フィールド別精度を整理
        field_accuracies = overall_summary.get('field_accuracies', {})
        field_accuracies_formatted = {
            field: "{:.1f}".format(accuracy * 100) 
            for field, accuracy in field_accuracies.items()
        }
        
        # データセット別サマリーを整理
        dataset_summary = overall_summary.get('dataset_summary', {})
        datasets = []
        for dataset_name, stats in dataset_summary.items():
            dataset_data = {
                'name': dataset_name,
                'experiment_count': stats.get('experiment_count', 0),
                'total_documents': stats.get('total_documents', 0),
                'total_successful': stats.get('total_successful', 0),
                'average_accuracy': stats.get('average_accuracy', 0.0),
                'average_accuracy_formatted': "{:.1f}".format(stats.get('average_accuracy', 0.0) * 100)
            }
            datasets.append(dataset_data)
        
        return {
            'report_title': report_title,
            'description': description,
            'generated_at': datetime.now().strftime('%Y年%m月%d日 %H:%M:%S'),
            'total_experiments': total_experiments,
            'total_documents': total_documents,
            'total_successful': total_successful,
            'total_failed': total_failed,
            'overall_accuracy': overall_accuracy,
            'overall_accuracy_formatted': "{:.1f}".format(overall_accuracy * 100),
            'field_accuracies': field_accuracies,
            'field_accuracies_formatted': field_accuracies_formatted,
            'datasets': datasets,
            'experiments': formatted_experiments
        }