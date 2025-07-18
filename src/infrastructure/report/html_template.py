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
        /* タブ機能のスタイル */
        .tabs-container {
            margin-bottom: 30px;
        }
        .tab-buttons {
            display: flex;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .tab-button {
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-bottom: none;
            padding: 12px 20px;
            cursor: pointer;
            margin-right: 2px;
            margin-bottom: -1px;
            border-radius: 5px 5px 0 0;
            transition: all 0.3s ease;
            font-weight: 500;
            color: #495057;
        }
        .tab-button:hover {
            background-color: #e9ecef;
        }
        .tab-button.active {
            background-color: white;
            border-bottom: 2px solid white;
            color: #2c3e50;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .tab-summary {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }
        .tab-summary h3 {
            margin: 0 0 10px 0;
            color: #2c3e50;
        }
        .tab-summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }
        .tab-summary-item {
            text-align: center;
            padding: 8px;
            background-color: white;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }
        .tab-summary-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .tab-summary-label {
            font-size: 0.8em;
            color: #666;
            margin-top: 4px;
        }
        
        @media print {
            body { background-color: white; }
            .container { box-shadow: none; }
            .tab-buttons { display: none; }
            .tab-content { display: block !important; }
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
        
        <!-- タブ機能 -->
        {% if results|length > 1 %}
        <div class="tabs-container">
            <div class="tab-buttons">
                {% for result in results %}
                <button class="tab-button {% if loop.first %}active{% endif %}" onclick="showTab('{{ result.document_id }}')">
                    {{ result.document_id }}
                </button>
                {% endfor %}
            </div>
            
            {% for result in results %}
            <div id="tab-{{ result.document_id }}" class="tab-content {% if loop.first %}active{% endif %}">
                <div class="tab-summary">
                    <h3>{{ result.document_id }}</h3>
                    <div class="tab-summary-grid">
                        <div class="tab-summary-item">
                            <div class="tab-summary-value">{{ "%.1f"|format(result.accuracy * 100) }}%</div>
                            <div class="tab-summary-label">精度</div>
                        </div>
                        <div class="tab-summary-item">
                            <div class="tab-summary-value">{% if result.is_success %}成功{% else %}失敗{% endif %}</div>
                            <div class="tab-summary-label">ステータス</div>
                        </div>
                        {% if result.extraction_time_ms %}
                        <div class="tab-summary-item">
                            <div class="tab-summary-value">{{ result.extraction_time_ms }}ms</div>
                            <div class="tab-summary-label">実行時間</div>
                        </div>
                        {% endif %}
                    </div>
                </div>
                
                <div class="document-result {% if result.accuracy >= 0.8 %}success{% else %}fail{% endif %}">
                    <div class="document-header {% if result.accuracy >= 0.8 %}success{% else %}fail{% endif %}">
                        <div>データセットID: {{ result.document_id }}</div>
                    </div>
                    
                    <div class="field-comparison">
                        {% if result.is_success %}
                        <table class="comparison-table">
                            <thead>
                                <tr>
                                    <th>フィールド</th>
                                    <th>期待値</th>
                                    <th>実際値</th>
                                </tr>
                            </thead>
                            <tbody>
                                {# まずitems以外のフィールドを表示 #}
                                {% for metric in result.field_results %}
                                {% if not metric.field_name.startswith('items.') %}
                                <tr>
                                    <td class="field-name">{{ metric.display_name if metric.display_name else metric.field_name }}</td>
                                    <td>
                                        {{ metric.expected_value if metric.expected_value != "" else "(空)" }}
                                    </td>
                                    <td>
                                        <span {% if not metric.is_correct %}class="value-mismatch"{% endif %}>
                                            {{ metric.actual_value if metric.actual_value != "" else "(空)" }}
                                        </span>
                                    </td>
                                </tr>
                                {% endif %}
                                {% endfor %}
                                
                                {# itemsフィールドをインデックスごとに階層表示 #}
                                {% set items_metrics = [] %}
                                {% for metric in result.field_results %}
                                {% if metric.field_name.startswith('items.') and metric.item_index is not none %}
                                {% set _ = items_metrics.append(metric) %}
                                {% endif %}
                                {% endfor %}
                                
                                {% if items_metrics %}
                                <tr>
                                    <td colspan="3" style="padding: 0; border: none;">
                                        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin: 10px 0;">
                                            <h4 style="margin: 0 0 15px 0; color: #2c3e50;">アイテム別詳細比較</h4>
                                            
                                            {# アイテムインデックスでグループ化 #}
                                            {% set unique_indexes = [] %}
                                            {% for metric in items_metrics %}
                                            {% if metric.item_index not in unique_indexes %}
                                            {% set _ = unique_indexes.append(metric.item_index) %}
                                            {% endif %}
                                            {% endfor %}
                                            
                                            {% for item_index in unique_indexes | sort %}
                                            <div style="margin-bottom: 25px; border: 1px solid #dee2e6; border-radius: 5px; overflow: hidden;">
                                                <div style="background-color: #e9ecef; padding: 10px; font-weight: bold; color: #2c3e50;">
                                                    アイテム {{ item_index + 1 }}
                                                </div>
                                                <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                                                    <thead>
                                                        <tr style="background-color: #f8f9fa;">
                                                            <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6; width: 25%;">フィールド</th>
                                                            <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6; width: 35%;">期待値</th>
                                                            <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6; width: 35%;">実際値</th>
                                                            <th style="padding: 8px; text-align: center; border: 1px solid #dee2e6; width: 5%;">一致</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {% for metric in items_metrics | selectattr('item_index', 'equalto', item_index) | sort(attribute='field_name') %}
                                                        <tr>
                                                            <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: 500;">
                                                                {{ metric.field_name.replace('items.', '') }}
                                                            </td>
                                                            <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                                {{ metric.expected_value if metric.expected_value != "" else "(空)" }}
                                                            </td>
                                                            <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                                <span {% if not metric.is_correct %}class="value-mismatch"{% endif %}>
                                                                    {{ metric.actual_value if metric.actual_value != "" else "(空)" }}
                                                                </span>
                                                            </td>
                                                            <td style="padding: 8px; border: 1px solid #dee2e6; text-align: center;">
                                                                {% if metric.is_correct %}
                                                                    <span style="color: #28a745; font-weight: bold;">✓</span>
                                                                {% else %}
                                                                    <span style="color: #dc3545; font-weight: bold;">✗</span>
                                                                {% endif %}
                                                            </td>
                                                        </tr>
                                                        {% endfor %}
                                                    </tbody>
                                                </table>
                                            </div>
                                            {% endfor %}
                                        </div>
                                    </td>
                                </tr>
                                {% endif %}
                            </tbody>
                        </table>
                        
                        {% else %}
                        <div class="error-message">
                            <strong>エラー:</strong> {{ result.error_message }}
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        
        {% for result in results %}
        <div class="document-result {% if result.accuracy >= 0.8 %}success{% else %}fail{% endif %}">
            <div class="document-header {% if result.accuracy >= 0.8 %}success{% else %}fail{% endif %}">
                <div>データセットID: {{ result.document_id }}</div>
            </div>
            
            <div class="field-comparison">
                {% if result.is_success %}
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>フィールド</th>
                            <th>期待値</th>
                            <th>実際値</th>
                        </tr>
                    </thead>
                    <tbody>
                        {# まずitems以外のフィールドを表示 #}
                        {% for metric in result.field_results %}
                        {% if not metric.field_name.startswith('items.') %}
                        <tr>
                            <td class="field-name">{{ metric.display_name if metric.display_name else metric.field_name }}</td>
                            <td>
                                {{ metric.expected_value if metric.expected_value != "" else "(空)" }}
                            </td>
                            <td>
                                <span {% if not metric.is_correct %}class="value-mismatch"{% endif %}>
                                    {{ metric.actual_value if metric.actual_value != "" else "(空)" }}
                                </span>
                            </td>
                        </tr>
                        {% endif %}
                        {% endfor %}
                        
                        {# itemsフィールドをインデックスごとに階層表示 #}
                        {% set items_metrics = [] %}
                        {% for metric in result.field_results %}
                        {% if metric.field_name.startswith('items.') and metric.item_index is not none %}
                        {% set _ = items_metrics.append(metric) %}
                        {% endif %}
                        {% endfor %}
                        
                        {% if items_metrics %}
                        <tr>
                            <td colspan="3" style="padding: 0; border: none;">
                                <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin: 10px 0;">
                                    <h4 style="margin: 0 0 15px 0; color: #2c3e50;">アイテム別詳細比較</h4>
                                    
                                    {# アイテムインデックスでグループ化 #}
                                    {% set unique_indexes = [] %}
                                    {% for metric in items_metrics %}
                                    {% if metric.item_index not in unique_indexes %}
                                    {% set _ = unique_indexes.append(metric.item_index) %}
                                    {% endif %}
                                    {% endfor %}
                                    
                                    {% for item_index in unique_indexes | sort %}
                                    <div style="margin-bottom: 25px; border: 1px solid #dee2e6; border-radius: 5px; overflow: hidden;">
                                        <div style="background-color: #e9ecef; padding: 10px; font-weight: bold; color: #2c3e50;">
                                            アイテム {{ item_index + 1 }}
                                        </div>
                                        <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                                            <thead>
                                                <tr style="background-color: #f8f9fa;">
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6; width: 25%;">フィールド</th>
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6; width: 35%;">期待値</th>
                                                    <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6; width: 35%;">実際値</th>
                                                    <th style="padding: 8px; text-align: center; border: 1px solid #dee2e6; width: 5%;">一致</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {% for metric in items_metrics | selectattr('item_index', 'equalto', item_index) | sort(attribute='field_name') %}
                                                <tr>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: 500;">
                                                        {{ metric.field_name.replace('items.', '') }}
                                                    </td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                        {{ metric.expected_value if metric.expected_value != "" else "(空)" }}
                                                    </td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                        <span {% if not metric.is_correct %}class="value-mismatch"{% endif %}>
                                                            {{ metric.actual_value if metric.actual_value != "" else "(空)" }}
                                                        </span>
                                                    </td>
                                                    <td style="padding: 8px; border: 1px solid #dee2e6; text-align: center;">
                                                        {% if metric.is_correct %}
                                                            <span style="color: #28a745; font-weight: bold;">✓</span>
                                                        {% else %}
                                                            <span style="color: #dc3545; font-weight: bold;">✗</span>
                                                        {% endif %}
                                                    </td>
                                                </tr>
                                                {% endfor %}
                                            </tbody>
                                        </table>
                                    </div>
                                    {% endfor %}
                                </div>
                            </td>
                        </tr>
                        {% endif %}
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
        {% endif %}
        

        <div class="timestamp">
            レポート生成日時: {{ report_generated_at }}
        </div>
    </div>

    <script>
        function showTab(documentId) {
            // 全てのタブコンテンツを非表示
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => {
                content.classList.remove('active');
            });
            
            // 全てのタブボタンを非アクティブ
            const tabButtons = document.querySelectorAll('.tab-button');
            tabButtons.forEach(button => {
                button.classList.remove('active');
            });
            
            // 指定されたタブコンテンツを表示
            const targetTab = document.getElementById('tab-' + documentId);
            if (targetTab) {
                targetTab.classList.add('active');
            }
            
            // 対応するタブボタンをアクティブ
            const targetButton = document.querySelector(`[onclick="showTab('${documentId}')"]`);
            if (targetButton) {
                targetButton.classList.add('active');
            }
        }
        
        // 初期化: 最初のタブをアクティブにする
        document.addEventListener('DOMContentLoaded', function() {
            const firstTabButton = document.querySelector('.tab-button');
            if (firstTabButton) {
                firstTabButton.click();
            }
        });
    </script>
</body>
</html>
"""

MULTI_DATASET_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>複数データセット実験結果レポート - {{ report_title }}</title>
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
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 20px;
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
        .field-accuracies {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .field-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .field-card {
            background-color: white;
            padding: 12px;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            text-align: center;
        }
        .field-value {
            font-size: 1.5em;
            font-weight: bold;
            margin: 5px 0;
        }
        .field-name {
            color: #666;
            font-size: 0.8em;
        }
        .dataset-items-section {
            margin-bottom: 30px;
        }
        .dataset-items-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }
        .dataset-item-card {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .dataset-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        .dataset-item-header h3 {
            margin: 0;
            color: #2c3e50;
            font-size: 1.1em;
            word-break: break-all;
        }
        .dataset-item-accuracy {
            text-align: center;
        }
        .accuracy-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #27ae60;
            display: block;
        }
        .accuracy-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .dataset-item-details {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .detail-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .detail-label {
            font-weight: 600;
            color: #495057;
            margin-right: 10px;
        }
        .detail-value {
            color: #6c757d;
            text-align: right;
        }
        .detail-value.success {
            color: #28a745;
            font-weight: bold;
        }
        .detail-value.error {
            color: #dc3545;
            font-weight: bold;
        }
        .datasets-section {
            margin-bottom: 30px;
        }
        .dataset-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .dataset-table th,
        .dataset-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .dataset-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .dataset-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .experiments-section {
            margin-bottom: 30px;
        }
        .experiment-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .experiment-table th,
        .experiment-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .experiment-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .experiment-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .accuracy-badge {
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: bold;
            color: white;
            font-size: 0.9em;
        }
        .accuracy-high { background-color: #28a745; }
        .accuracy-medium { background-color: #ffc107; }
        .accuracy-low { background-color: #dc3545; }
        .status-badge {
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-completed { background-color: #d4edda; color: #155724; }
        .status-failed { background-color: #f8d7da; color: #721c24; }
        .status-running { background-color: #d1ecf1; color: #0c5460; }
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report_title }}</h1>
            {% if description %}
            <p>{{ description }}</p>
            {% endif %}
        </div>
        
        <!-- 全体サマリー -->
        <div class="summary">
            <h2>全体サマリー</h2>
            <div class="summary-grid">
                <div class="metric-card">
                    <div class="metric-value">{{ total_experiments }}</div>
                    <div class="metric-label">実験数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ total_documents }}</div>
                    <div class="metric-label">総ドキュメント数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ total_successful }}</div>
                    <div class="metric-label">成功数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ total_failed }}</div>
                    <div class="metric-label">失敗数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ overall_accuracy_formatted }}%</div>
                    <div class="metric-label">全体精度</div>
                </div>
            </div>
        </div>
        
        <!-- フィールド別精度 -->
        {% if field_accuracies %}
        <div class="field-accuracies">
            <h2>フィールド別精度</h2>
            <div class="field-grid">
                {% for field, accuracy in field_accuracies_formatted.items() %}
                <div class="field-card">
                    <div class="field-value">{{ accuracy }}%</div>
                    <div class="field-name">{{ field }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <!-- データセット別サマリー -->
        {% if datasets %}
        <div class="datasets-section">
            <h2>データセット別サマリー</h2>
            <table class="dataset-table">
                <thead>
                    <tr>
                        <th>データセット名</th>
                        <th>実験数</th>
                        <th>ドキュメント数</th>
                        <th>成功数</th>
                        <th>平均精度</th>
                    </tr>
                </thead>
                <tbody>
                    {% for dataset in datasets %}
                    <tr>
                        <td>{{ dataset.name }}</td>
                        <td>{{ dataset.experiment_count }}</td>
                        <td>{{ dataset.total_documents }}</td>
                        <td>{{ dataset.total_successful }}</td>
                        <td>{{ dataset.average_accuracy_formatted }}%</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <!-- 実験結果一覧 -->
        <div class="experiments-section">
            <h2>実験結果一覧</h2>
            <table class="experiment-table">
                <thead>
                    <tr>
                        <th>実験名</th>
                        <th>データセット</th>
                        <th>LLMエンドポイント</th>
                        <th>ステータス</th>
                        <th>ドキュメント数</th>
                        <th>成功数</th>
                        <th>失敗数</th>
                        <th>精度</th>
                        <th>完了日時</th>
                    </tr>
                </thead>
                <tbody>
                    {% for experiment in experiments %}
                    <tr>
                        <td>{{ experiment.name }}</td>
                        <td>{{ experiment.dataset_name }}</td>
                        <td>{{ experiment.llm_endpoint }}</td>
                        <td>
                            <span class="status-badge status-{{ experiment.status }}">
                                {{ experiment.status }}
                            </span>
                        </td>
                        <td>{{ experiment.total_documents }}</td>
                        <td>{{ experiment.successful_count }}</td>
                        <td>{{ experiment.failed_count }}</td>
                        <td>
                            {% set accuracy = experiment.overall_accuracy * 100 %}
                            <span class="accuracy-badge 
                                {% if accuracy >= 80 %}accuracy-high
                                {% elif accuracy >= 50 %}accuracy-medium
                                {% else %}accuracy-low{% endif %}">
                                {{ experiment.overall_accuracy_formatted }}%
                            </span>
                        </td>
                        <td>{{ experiment.completed_at }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="timestamp">
            レポート生成日時: {{ generated_at }}
        </div>
    </div>
</body>
</html>
"""