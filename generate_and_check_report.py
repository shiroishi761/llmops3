#!/usr/bin/env python3
"""既存の結果ファイルからHTMLレポートを生成し、主要部分を表示するスクリプト"""

import json
from pathlib import Path
from src.infrastructure.report.html_report_generator import HTMLReportGenerator
import re

def extract_section(html_content, start_pattern, end_pattern=None):
    """HTMLから特定のセクションを抽出"""
    start_match = re.search(start_pattern, html_content, re.DOTALL | re.IGNORECASE)
    if not start_match:
        return None
    
    start_pos = start_match.start()
    
    if end_pattern:
        end_match = re.search(end_pattern, html_content[start_pos:], re.DOTALL | re.IGNORECASE)
        if end_match:
            end_pos = start_pos + end_match.start()
            return html_content[start_pos:end_pos]
    
    return html_content[start_pos:]

def extract_table_data(table_html):
    """HTMLテーブルからデータを抽出"""
    # ヘッダー行を抽出
    header_match = re.search(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
    headers = []
    if header_match:
        header_content = header_match.group(1)
        th_matches = re.findall(r'<th[^>]*>(.*?)</th>', header_content, re.DOTALL | re.IGNORECASE)
        headers = [re.sub(r'<[^>]+>', '', th).strip() for th in th_matches]
    
    # データ行を抽出
    rows = []
    tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)[1:]  # 最初の行（ヘッダー）をスキップ
    for tr_content in tr_matches[:5]:  # 最初の5行のみ
        td_matches = re.findall(r'<td[^>]*>(.*?)</td>', tr_content, re.DOTALL | re.IGNORECASE)
        cells = [re.sub(r'<[^>]+>', '', td).strip() for td in td_matches]
        if cells:
            rows.append(cells)
    
    return headers, rows

def main():
    # 結果ファイルのパス
    result_file = Path("/Users/apple/llmops/results/消火設備見積書データ抽出テスト_Gemini1.5_20250706_162758.json")
    
    print(f"結果ファイルを読み込み中: {result_file}")
    
    # 結果ファイルを読み込む
    with open(result_file, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    
    # HTMLレポートを生成
    try:
        generator = HTMLReportGenerator()
        output_path_str = generator.generate(result_data)  # generateメソッドはファイルパスを返す
        output_path = Path(output_path_str)
        
        print(f"\nHTMLレポートを生成しました: {output_path}")
        
        # 生成されたHTMLファイルを読み込む
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"生成されたHTMLの長さ: {len(html_content)} 文字")
        
    except Exception as e:
        print(f"エラーが発生しました: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # サマリーセクションを抽出
    print("\n=== サマリーセクション ===")
    summary_section = extract_section(html_content, r'<div class="summary"[^>]*>', r'</div>')
    if summary_section:
        # HTMLタグを除去してテキストを表示
        summary_text = re.sub(r'<[^>]+>', ' ', summary_section)
        summary_text = re.sub(r'\s+', ' ', summary_text).strip()
        print(summary_text)
        
        # HTMLも表示（最初の500文字）
        print("\n--- サマリーHTML ---")
        print(summary_section[:500] + "..." if len(summary_section) > 500 else summary_section)
    
    # アイテム比較セクションを抽出
    print("\n=== アイテム比較セクション ===")
    # h3タグで「アイテム比較」を探す
    items_section = extract_section(html_content, r'<h3[^>]*>アイテム比較</h3>', r'<h3')
    if items_section:
        # テーブルを抽出
        table_match = re.search(r'<table[^>]*>(.*?)</table>', items_section, re.DOTALL | re.IGNORECASE)
        if table_match:
            table_html = table_match.group(0)
            headers, rows = extract_table_data(table_html)
            
            print("\n--- アイテム比較テーブル ---")
            print("ヘッダー:", headers)
            
            for i, row in enumerate(rows, 1):
                print(f"行{i}: {row}")
            
            if len(rows) == 5:
                print("... (残りの行は省略)")
            
            # HTMLも表示（最初の1000文字）
            print("\n--- アイテム比較HTML（最初の部分） ---")
            print(table_html[:1000] + "..." if len(table_html) > 1000 else table_html)
    
    # 「アイテム精度」が含まれていないことを確認
    print("\n=== 「アイテム精度」の確認 ===")
    if 'アイテム精度' in html_content:
        print("❌ エラー: HTMLに「アイテム精度」が含まれています")
        # どこに含まれているか調査
        lines = html_content.split('\n')
        for i, line in enumerate(lines):
            if 'アイテム精度' in line:
                print(f"  行{i+1}: {line.strip()}")
    else:
        print("✅ OK: HTMLに「アイテム精度」は含まれていません")
    
    # 総合スコアセクションを確認
    print("\n=== 総合スコア情報 ===")
    score_pattern = r'総合スコア[:\s]*([0-9.]+)%'
    score_match = re.search(score_pattern, html_content)
    if score_match:
        print(f"総合スコア: {score_match.group(1)}%")

if __name__ == "__main__":
    main()