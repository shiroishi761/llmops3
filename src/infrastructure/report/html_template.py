"""HTMLレポートテンプレート"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>実験結果レポート - {{ experiment_name }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .summary {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }
        .metric-card {
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin: 5px 0;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        .document-result {
            margin-bottom: 40px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .document-result.success {
            border: 2px solid #28a745;
            background-color: #f8fffe;
        }
        .document-result.fail {
            border: 2px solid #007bff;
            background-color: #f0f8ff;
        }
        .document-header {
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
            font-size: 1.1em;
        }
        .document-header.success {
            background-color: #d4edda;
            color: #155724;
        }
        .document-header.fail {
            background-color: #cfe2ff;
            color: #052c65;
        }
        .accuracy-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }
        .accuracy-high { background-color: #28a745; }
        .accuracy-medium { background-color: #ffc107; }
        .accuracy-low { background-color: #dc3545; }
        .field-comparison {
            padding: 20px;
        }
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .comparison-table th {
            background-color: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: bold;
            border-bottom: 2px solid #dee2e6;
        }
        .comparison-table th:nth-child(1) { width: 20%; }
        .comparison-table th:nth-child(2) { width: 40%; }
        .comparison-table th:nth-child(3) { width: 40%; }
        .comparison-table td {
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }
        .comparison-table tr:hover {
            background-color: #f8f9fa;
        }
        .field-name {
            font-weight: 600;
            color: #495057;
        }
        .value-mismatch {
            color: #dc3545;
            font-weight: bold;
        }
        .items-section {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        .items-matching-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 0.9em;
        }
        .items-matching-table th {
            background-color: #e9ecef;
            padding: 8px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #dee2e6;
        }
        .items-matching-table td {
            padding: 8px;
            border: 1px solid #dee2e6;
            vertical-align: top;
        }
        .match-group {
            background-color: #f8f9fa;
        }
        .match-status {
            text-align: center;
            font-weight: bold;
        }
        .match-high { color: #28a745; }
        .match-medium { color: #ffc107; }
        .match-low { color: #dc3545; }
        .match-none { color: #6c757d; }
        .item-expected {
            background-color: #e3f2fd;
        }
        .item-actual {
            background-color: #e8f5e9;
        }
        .item-field-match {
            color: #28a745;
            font-weight: bold;
        }
        .item-field-mismatch {
            color: #dc3545;
            font-weight: bold;
        }
        .match-reason {
            font-size: 0.85em;
            color: #6c757d;
            font-style: italic;
        }
        .error-message {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 12px 20px;
            border-radius: 4px;
            margin-top: 10px;
        }
        .timestamp {
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 30px;
            text-align: center;
        }
        @media print {
            body { background-color: white; }
            .container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="summary">
            <p><strong>実験名:</strong> {{ experiment_name }}</p>
            <p><strong>プロンプト:</strong> {{ prompt_name }}</p>
            <p><strong>データセット:</strong> {{ dataset_name }}</p>
            <p><strong>LLMエンドポイント:</strong> {{ llm_endpoint }}</p>
            <p><strong>実行日時:</strong> {{ created_at }} 〜 {{ completed_at }}</p>
            
            <div class="summary-grid">
                <div class="metric-card">
                    <div class="metric-label">スコア</div>
                    <div class="metric-value" style="color: {% if max_possible_score > 0 and overall_score / max_possible_score >= 0.8 %}#28a745{% elif max_possible_score > 0 and overall_score / max_possible_score >= 0.6 %}#ffc107{% else %}#dc3545{% endif %}">
                        {{ "%.1f" | format(overall_score) }} / {{ "%.1f" | format(max_possible_score) }}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">処理文書数</div>
                    <div class="metric-value">{{ total_documents }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">成功数</div>
                    <div class="metric-value" style="color: #28a745">{{ successful_count }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">失敗数</div>
                    <div class="metric-value" style="color: #dc3545">{{ failed_count }}</div>
                </div>
            </div>
        </div>
        
        {% for result in results %}
        <div class="document-result {% if not result.error_message %}success{% else %}fail{% endif %}">
            <div class="document-header {% if not result.error_message %}success{% else %}fail{% endif %}">
                <div>データセットID: {{ result.document_id }}</div>
            </div>
            
            <div class="field-comparison">
                {% if not result.error_message %}
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>フィールド</th>
                            <th>期待値</th>
                            <th>実際値</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for metric in result.accuracy_metrics %}
                        <tr>
                            <td class="field-name">{{ metric.field_name }}</td>
                            {% if metric.property_comparisons %}
                                {# オブジェクト型フィールドの詳細比較 #}
                                <td colspan="2" style="padding: 0;">
                                    <div style="padding: 15px;">
                                        <h4 style="margin: 0 0 10px 0;">{{ metric.field_name }}の詳細比較</h4>
                                        <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                                            <thead>
                                                <tr style="background-color: #e9ecef;">
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6; width: 30%;">プロパティ</th>
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6; width: 30%;">期待値</th>
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6; width: 30%;">実際値</th>
                                                    <th style="padding: 8px; text-align: center; border: 1px solid #dee2e6; width: 10%;">一致</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {% for comp in metric.property_comparisons %}
                                                <tr>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">{{ comp.property_name }}</td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                        {{ comp.expected_value if comp.expected_value is not none else "(なし)" }}
                                                    </td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                        <span {% if not comp.is_match %}class="value-mismatch"{% endif %}>
                                                            {{ comp.actual_value if comp.actual_value is not none else "(なし)" }}
                                                        </span>
                                                    </td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; text-align: center;">
                                                        {% if comp.is_match %}
                                                            <span style="color: #28a745; font-weight: bold;">✓</span>
                                                        {% else %}
                                                            <span style="color: #dc3545; font-weight: bold;">✗</span>
                                                        {% endif %}
                                                    </td>
                                                </tr>
                                                {% endfor %}
                                            </tbody>
                                        </table>
                                        <div style="margin-top: 10px; text-align: right;">
                                            <strong>全体精度:</strong>
                                            <span {% if metric.object_accuracy < 0.8 %}class="value-mismatch"{% endif %} style="font-size: 1.1em;">
                                                {{ "%.0f" | format(metric.object_accuracy * 100) }}%
                                            </span>
                                        </div>
                                    </div>
                                </td>
                            {% elif metric.field_name == 'items' %}
                                <td colspan="4" style="padding: 0;">
                                    {% if metric.items_matches %}
                                    <div style="padding: 15px;">
                                        <h4 style="margin: 0 0 10px 0;">アイテム明細の比較</h4>
                                        <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                                            <thead>
                                                <tr style="background-color: #e9ecef;">
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">項目</th>
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">name</th>
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">spec</th>
                                                    <th style="padding: 8px; text-align: center; border: 1px solid #dee2e6;">quantity</th>
                                                    <th style="padding: 8px; text-align: center; border: 1px solid #dee2e6;">unit</th>
                                                    <th style="padding: 8px; text-align: right; border: 1px solid #dee2e6;">price</th>
                                                    <th style="padding: 8px; text-align: right; border: 1px solid #dee2e6;">sub_total</th>
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">note</th>
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">account_item</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {% for match in metric.items_matches %}
                                                <tr style="background-color: #e3f2fd;">
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">期待値</td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6;">{{ match.expected.name }}</td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6;">{{ match.expected.spec if match.expected.spec else "-" }}</td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; text-align: center;">{{ match.expected.quantity }}</td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; text-align: center;">{{ match.expected.unit if match.expected.unit else "-" }}</td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">{{ "{:,}".format(match.expected.price) if match.expected.price else "0" }}円</td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">{{ "{:,}".format(match.expected.sub_total) if match.expected.sub_total else "0" }}円</td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6;">{{ match.expected.note if match.expected.note else "-" }}</td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6;">{{ match.expected.account_item if match.expected.account_item else "-" }}</td>
                                                </tr>
                                                <tr style="background-color: #e8f5e9;">
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">実際値</td>
                                                    {% if match.matched %}
                                                        <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                            <span class="{% if match.field_matches.name %}item-field-match{% else %}item-field-mismatch{% endif %}">
                                                                {{ match.matched.name }}
                                                            </span>
                                                        </td>
                                                        <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                            <span class="{% if match.field_matches.spec is not defined or match.field_matches.spec %}item-field-match{% else %}item-field-mismatch{% endif %}">
                                                                {{ match.matched.spec if match.matched.spec else "-" }}
                                                            </span>
                                                        </td>
                                                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: center;">
                                                            <span class="{% if match.field_matches.quantity %}item-field-match{% else %}item-field-mismatch{% endif %}">
                                                                {{ match.matched.quantity }}
                                                            </span>
                                                        </td>
                                                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: center;">
                                                            <span class="{% if match.field_matches.unit %}item-field-match{% else %}item-field-mismatch{% endif %}">
                                                                {{ match.matched.unit if match.matched.unit else "-" }}
                                                            </span>
                                                        </td>
                                                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">
                                                            <span class="{% if match.field_matches.price is not defined or match.expected.price == match.matched.price %}item-field-match{% else %}item-field-mismatch{% endif %}">
                                                                {{ "{:,}".format(match.matched.price) if match.matched.price else "0" }}円
                                                            </span>
                                                        </td>
                                                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">
                                                            <span class="{% if match.field_matches.sub_total is not defined or match.expected.sub_total == match.matched.sub_total %}item-field-match{% else %}item-field-mismatch{% endif %}">
                                                                {{ "{:,}".format(match.matched.sub_total) if match.matched.sub_total else "0" }}円
                                                            </span>
                                                        </td>
                                                        <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                            <span class="{% if match.field_matches.note %}item-field-match{% else %}item-field-mismatch{% endif %}">
                                                                {{ match.matched.note if match.matched.note else "-" }}
                                                            </span>
                                                        </td>
                                                        <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                            <span class="{% if match.field_matches.account_item %}item-field-match{% else %}item-field-mismatch{% endif %}">
                                                                {{ match.matched.account_item if match.matched.account_item else "-" }}
                                                            </span>
                                                        </td>
                                                    {% else %}
                                                        <td colspan="8" style="padding: 8px; border: 1px solid #dee2e6; text-align: center; color: #6c757d; font-style: italic;">
                                                            マッチするアイテムなし
                                                        </td>
                                                    {% endif %}
                                                </tr>
                                                {% if not loop.last %}
                                                <tr><td colspan="9" style="height: 10px; border: none;"></td></tr>
                                                {% endif %}
                                                {% endfor %}
                                            </tbody>
                                        </table>
                                    </div>
                                    {% else %}
                                        {{ metric.expected_value if metric.expected_value != "" else "(空)" }}
                                    {% endif %}
                                </td>
                            {% else %}
                                <td>
                                    {{ metric.expected_value if metric.expected_value != "" else "(空)" }}
                                </td>
                                <td>
                                    <span {% if not metric.is_correct %}class="value-mismatch"{% endif %}>
                                        {{ metric.actual_value if metric.actual_value != "" else "(空)" }}
                                    </span>
                                </td>
                            {% endif %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                
                {% else %}
                <div class="error-message">
                    <strong>エラー:</strong> {{ result.error_message }}
                </div>
                {% endif %}
            </div>
        </div>
        {% endfor %}
        
        <div class="timestamp">
            レポート生成日時: {{ report_generated_at }}
        </div>
    </div>
</body>
</html>
"""
