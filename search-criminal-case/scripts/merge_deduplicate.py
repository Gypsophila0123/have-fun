#!/usr/bin/env python3
"""
merge_deduplicate.py — 多源检索结果合并与去重工具

用途：Phase 3 将北大法宝语义检索、关键词检索和本地案例库的结果合并、去重、质量筛选
依赖：无外部依赖（纯标准库）

用法：
    python merge_deduplicate.py --input results_semantic.json results_keyword.json results_local.json --output merged.json
"""

import argparse
import json
import sys
from pathlib import Path


def load_cases(file_path):
    """Load case list from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "cases" in data:
        return data["cases"]
    elif isinstance(data, dict) and "results" in data:
        return data["results"]
    else:
        return [data]


def normalize_case_number(case_number):
    """Normalize case number for deduplication."""
    if not case_number:
        return ""
    # Remove whitespace and normalize parentheses
    normalized = case_number.strip()
    normalized = normalized.replace("（", "(").replace("）", ")")
    normalized = normalized.replace(" ", "").replace("\t", "")
    return normalized.lower()


def deduplicate_cases(cases):
    """Remove duplicate cases by case number + charge."""
    seen = set()
    unique = []
    duplicates = 0

    for case in cases:
        case_number = case.get("case_number", "") or case.get("案号", "") or case.get("id", "")
        charge = case.get("charge", "") or case.get("罪名", "") or case.get("判定罪名", "") or case.get("指控罪名", "") or ""
        normalized_number = normalize_case_number(case_number)
        
        dedup_key = f"{normalized_number}_{charge}" if normalized_number else ""

        if dedup_key and dedup_key in seen:
            duplicates += 1
            # Merge: keep the one with more data
            existing_idx = None
            for i, c in enumerate(unique):
                c_num = c.get("case_number", "") or c.get("案号", "") or c.get("id", "")
                c_charge = c.get("charge", "") or c.get("罪名", "") or c.get("判定罪名", "") or c.get("指控罪名", "") or ""
                existing_key = f"{normalize_case_number(c_num)}_{c_charge}"
                if existing_key == dedup_key:
                    existing_idx = i
                    break
            if existing_idx is not None:
                existing = unique[existing_idx]
                # Merge fields: prefer non-empty values
                for key in set(list(case.keys()) + list(existing.keys())):
                    if key not in existing or not existing.get(key):
                        if case.get(key):
                            existing[key] = case[key]
            continue

        seen.add(dedup_key)
        unique.append(case)

    return unique, duplicates


def quality_filter(cases):
    """Filter out non-substantive judgments."""
    excluded_types = {
        "调解书", "撤诉裁定", "管辖权异议", "不予受理",
        "终止审理", "准许撤诉", "驳回起诉",
    }

    filtered = []
    excluded = 0

    for case in cases:
        doc_type = case.get("document_type", "") or case.get("文书类型", "") or ""

        # Check if should be excluded
        should_exclude = False
        for exc_type in excluded_types:
            if exc_type in doc_type:
                should_exclude = True
                break

        if should_exclude:
            excluded += 1
            continue

        # Mark guiding/typical cases
        case_title = case.get("title", "") or case.get("标题", "") or ""
        case_number = case.get("case_number", "") or case.get("案号", "") or ""
        is_guiding = "指导性" in case_title or "指导案例" in case_title
        is_typical = "典型案例" in case_title or "参考案例" in case_title

        case["priority"] = "guiding" if is_guiding else ("typical" if is_typical else "normal")

        filtered.append(case)

    return filtered, excluded


def tag_source(cases, source_name):
    """Tag each case with its source."""
    for case in cases:
        if "sources" not in case:
            case["sources"] = []
        if source_name not in case["sources"]:
            case["sources"].append(source_name)
    return cases


def merge_results(input_files):
    """Merge results from multiple source files."""
    all_cases = []

    for file_path in input_files:
        source_name = Path(file_path).stem
        try:
            cases = load_cases(file_path)
            cases = tag_source(cases, source_name)
            all_cases.extend(cases)
            print(f"  Loaded {len(cases)} cases from {file_path}")
        except Exception as e:
            print(f"  Warning: Failed to load {file_path}: {e}")

    print(f"\n  Total cases before dedup: {len(all_cases)}")

    # Deduplicate
    unique_cases, dup_count = deduplicate_cases(all_cases)
    print(f"  Removed {dup_count} duplicates")
    print(f"  Cases after dedup: {len(unique_cases)}")

    # Quality filter
    filtered_cases, excluded_count = quality_filter(unique_cases)
    print(f"  Excluded {excluded_count} non-substantive documents")
    print(f"  Valid cases: {len(filtered_cases)}")

    # Count by priority
    guiding = sum(1 for c in filtered_cases if c.get("priority") == "guiding")
    typical = sum(1 for c in filtered_cases if c.get("priority") == "typical")
    print(f"  Guiding cases: {guiding}, Typical cases: {typical}")

    return filtered_cases


def main():
    parser = argparse.ArgumentParser(description="Merge and deduplicate case search results")
    parser.add_argument("--input", "-i", nargs="+", required=True,
                        help="Input JSON files (semantic, keyword, local results)")
    parser.add_argument("--output", "-o", required=True, help="Output merged JSON file")
    args = parser.parse_args()

    print("Merging and deduplicating case results...")
    merged = merge_results(args.input)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"cases": merged, "total": len(merged)}, f, ensure_ascii=False, indent=2)

    print(f"\nMerged results saved to: {output_path}")
    print(f"Total valid cases: {len(merged)}")


if __name__ == "__main__":
    main()
