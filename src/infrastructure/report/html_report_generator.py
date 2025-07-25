"""HTMLレポート生成サービス"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Template
import json

from .html_template import HTML_TEMPLATE


class HTMLReportGenerator:
    """実験結果のHTMLレポートを生成するサービス"""
    
    def __init__(self, output_dir: Path = Path("reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.template = Template(HTML_TEMPLATE)
    
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
            
            # 新しいDTOベースの形式から精度を計算
            if 'field_results' in processed_result and processed_result['field_results']:
                # field_resultsから精度を計算
                total_score = sum(fr.get('score', 0) for fr in processed_result['field_results'])
                total_weight = sum(fr.get('weight', 0) for fr in processed_result['field_results'])
                accuracy = total_score / total_weight if total_weight > 0 else 0.0
                processed_result['accuracy'] = accuracy
                processed_result['accuracy_formatted'] = "{:.1f}".format(accuracy * 100)
                
                # field_resultsをaccuracy_metricsに変換
                accuracy_metrics = []
                for fr in processed_result['field_results']:
                    accuracy_metrics.append({
                        'field_name': fr.get('field_name', ''),
                        'expected_value': fr.get('expected_value'),
                        'actual_value': fr.get('actual_value'),
                        'score': fr.get('score', 0),
                        'weight': fr.get('weight', 0),
                        'is_correct': fr.get('is_correct', False)
                    })
                processed_result['accuracy_metrics'] = accuracy_metrics
            else:
                # 精度情報がない場合のデフォルト値
                processed_result['accuracy'] = 0.0
                processed_result['accuracy_formatted'] = "0.0"
                processed_result['accuracy_metrics'] = []
            
            # accuracy_metricsを処理して、フィールドを固定順序で並べ替える
            if 'accuracy_metrics' in processed_result:
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
                
                # メトリクスを辞書に変換
                metrics_dict = {m.get('field_name', getattr(m, 'field_name', None)): m for m in processed_result['accuracy_metrics']}
                
                # 順序に従って並べ替え
                sorted_metrics = []
                for field in field_order:
                    if field in metrics_dict:
                        sorted_metrics.append(metrics_dict[field])
                
                # field_orderに含まれていないフィールドも追加（items.*フィールドは除外）
                for field, metric in metrics_dict.items():
                    if field not in field_order and field != 'items' and not field.startswith('items.'):
                        sorted_metrics.insert(-1, metric)  # itemsの前に挿入
                
                processed_result['accuracy_metrics'] = sorted_metrics
            
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