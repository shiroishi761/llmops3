"""結果フォーマッタユーティリティ"""
from typing import List, Dict, Any
from collections import defaultdict

def format_experiment_results(experiment_data: dict) -> dict:
    """実験結果を構造化された形式にフォーマット"""
    # 基本情報をコピー
    formatted = {
        "id": experiment_data["id"],
        "name": experiment_data["name"],
        "prompt_name": experiment_data["prompt_name"],
        "dataset_name": experiment_data["dataset_name"],
        "llm_endpoint": experiment_data["llm_endpoint"],
        "description": experiment_data.get("description", ""),
        "status": experiment_data["status"],
        "created_at": experiment_data.get("created_at"),
        "started_at": experiment_data.get("started_at"),
        "completed_at": experiment_data.get("completed_at"),
        "error_message": experiment_data.get("error_message"),
        # プロンプト設定を記録（シンプル形式と複雑な形式の両方に対応）
        "prompt_configuration": experiment_data.get("prompt_configuration", {
            "type": "simple",
            "prompt_name": experiment_data["prompt_name"]
        })
    }
    
    # 結果を構造化
    formatted_results = []
    total_score = 0.0
    max_possible_score = 0.0
    
    for result in experiment_data.get("results", []):
        formatted_doc = format_document_result(result)
        formatted_results.append(formatted_doc)
        
        if not formatted_doc.get("error"):
            total_score += formatted_doc["summary"]["total_score"]
            max_possible_score += formatted_doc["summary"]["max_possible_score"]
    
    formatted["results"] = formatted_results
    
    # 全体サマリー
    overall_accuracy = total_score / max_possible_score if max_possible_score > 0 else 0.0
    formatted["summary"] = {
        "total_documents": len(formatted_results),
        "successful_documents": sum(1 for r in formatted_results if not r.get("error")),
        "failed_documents": sum(1 for r in formatted_results if r.get("error")),
        "overall_accuracy": overall_accuracy,
        "total_score": total_score,
        "max_possible_score": max_possible_score
    }
    
    # フィールド別集計
    formatted["field_summary"] = calculate_field_summary(formatted_results)
    
    return formatted

def format_document_result(doc_result: dict) -> dict:
    """ドキュメント結果を構造化"""
    formatted = {
        "document_id": doc_result["document_id"],
        "extraction_time_ms": doc_result.get("extraction_time_ms", 0),
        "error": doc_result.get("error")
    }
    
    if doc_result.get("error"):
        return formatted
    
    # フィールド結果を分類
    general_fields = []
    items_by_index = defaultdict(list)
    
    total_score = 0.0
    max_possible_score = 0.0
    
    for field_result in doc_result.get("field_results", []):
        # フィールド情報を簡潔に
        field_info = {
            "field": field_result["field_name"],
            "expected": field_result["expected_value"],
            "actual": field_result["actual_value"],
            "correct": field_result["is_correct"],
            "score": field_result["score"],
            "weight": field_result["weight"]
        }
        
        # スコア集計
        weighted_score = field_result["score"] * field_result["weight"]
        max_weighted_score = field_result["weight"]
        total_score += weighted_score
        max_possible_score += max_weighted_score
        
        # itemsフィールドの分類
        if field_result["field_name"].startswith("items.") and field_result.get("item_index") is not None:
            # "items.name[0]" -> "name"の形式で簡潔に
            field_name_parts = field_result["field_name"].split(".")
            if len(field_name_parts) >= 2:
                field_name = field_name_parts[1].split("[")[0]  # "[0]"部分を除去
                field_info["field"] = field_name
                items_by_index[field_result["item_index"]].append(field_info)
        else:
            general_fields.append(field_info)
    
    # 明細項目を構造化
    items_results = []
    for idx in sorted(items_by_index.keys()):
        fields = items_by_index[idx]
        
        # アイテムごとのスコア
        item_score = sum(f["score"] * f["weight"] for f in fields)
        item_max_score = sum(f["weight"] for f in fields)
        item_accuracy = item_score / item_max_score if item_max_score > 0 else 0.0
        
        items_results.append({
            "index": idx,
            "fields": fields,
            "accuracy": item_accuracy,
            "score": item_score,
            "max_score": item_max_score
        })
    
    # 全体精度
    overall_accuracy = total_score / max_possible_score if max_possible_score > 0 else 0.0
    
    formatted["fields"] = general_fields
    formatted["items"] = items_results
    formatted["summary"] = {
        "overall_accuracy": overall_accuracy,
        "total_score": total_score,
        "max_possible_score": max_possible_score
    }
    
    return formatted

def calculate_field_summary(formatted_results: List[dict]) -> dict:
    """フィールド別の集計"""
    field_stats = defaultdict(lambda: {"correct": 0, "total": 0, "weight_sum": 0.0})
    
    for doc in formatted_results:
        if doc.get("error"):
            continue
        
        # 一般フィールド
        for field in doc.get("fields", []):
            name = field["field"]
            stats = field_stats[name]
            stats["total"] += 1
            stats["weight_sum"] += field["weight"]
            if field["correct"]:
                stats["correct"] += 1
        
        # 明細項目フィールド
        for item in doc.get("items", []):
            for field in item["fields"]:
                name = f"items.{field['field']}"
                stats = field_stats[name]
                stats["total"] += 1
                stats["weight_sum"] += field["weight"]
                if field["correct"]:
                    stats["correct"] += 1
    
    # 精度計算
    summary = {}
    for field_name, stats in field_stats.items():
        if stats["total"] > 0:
            accuracy = stats["correct"] / stats["total"]
            avg_weight = stats["weight_sum"] / stats["total"]
            summary[field_name] = {
                "accuracy": accuracy,
                "avg_weight": avg_weight,
                "evaluations": stats["total"]
            }
    
    return summary