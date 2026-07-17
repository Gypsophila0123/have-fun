#!/usr/bin/env python3
"""
save_to_local.py — 案例入库工具

用途：将 MCP 检索结果中用户选择的案例保存到本地案例库，供下次检索复用

用法：
    python save_to_local.py --input merged.json --case-numbers '(2023)京0108刑初1234号' '(2023)沪01刑初5678号' --local-db input/local/local_database.json
    python save_to_local.py --input merged.json --all --local-db input/local/local_database.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


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
    """Normalize case number for comparison."""
    if not case_number:
        return ""
    normalized = case_number.strip()
    normalized = normalized.replace("（", "(").replace("）", ")")
    normalized = normalized.replace(" ", "").replace("\t", "")
    return normalized.lower()


def load_local_database(db_path):
    """Load existing local database, create empty if not exists."""
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump({"cases": [], "metadata": {"version": "1.0", "last_updated": "", "total_cases": 0}}, f, ensure_ascii=False, indent=2)
        return []
    
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "cases" in data:
            return data["cases"]
        else:
            return []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_local_database(db_path, cases):
    """Save cases to local database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "cases": cases,
        "metadata": {
            "version": "1.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_cases": len(cases)
        }
    }
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_charge_short_name(charge):
    """Get short name for charge."""
    if not charge:
        return "未知罪名"
    charge = charge.strip()
    if "非法获取" in charge and "数据" in charge:
        return "获取数据"
    elif "非法控制" in charge:
        return "非法控制"
    elif "非法侵入" in charge:
        return "侵入"
    elif "破坏" in charge:
        return "破坏"
    elif "提供" in charge and ("程序" in charge or "工具" in charge):
        return "提供程序工具"
    else:
        return charge[:4]


def save_case_as_txt(case, txt_dir):
    """Save a single case as txt file."""
    case_number = case.get("case_number", "") or case.get("案号", "") or "unknown"
    charge = case.get("charge", "") or case.get("罪名", "") or ""
    short_name = get_charge_short_name(charge)
    
    safe_case_number = case_number.replace("\\", "_").replace("/", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace('"', "_").replace("<", "_").replace(">", "_").replace("|", "_")
    filename = f"{safe_case_number}_{short_name}.txt"
    filepath = txt_dir / filename
    
    content = []
    content.append(f"案号: {case_number}")
    content.append(f"罪名: {charge}")
    content.append(f"标题: {case.get('title', '') or case.get('标题', '') or ''}")
    content.append(f"法院: {case.get('court', '') or case.get('法院', '') or ''}")
    content.append(f"判决日期: {case.get('verdict_date', '') or case.get('判决日期', '') or ''}")
    content.append(f"量刑: {case.get('sentence', '') or case.get('量刑', '') or ''}")
    content.append(f"来源: {case.get('source', '') or case.get('来源', '') or ''}")
    content.append("")
    content.append("摘要:")
    content.append(case.get('summary', '') or case.get('摘要', '') or case.get('ascertain', '') or case.get('查明事实', '') or "")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    
    return filepath


def save_cases_to_local(input_file, case_numbers, db_path, save_all=False, save_txt=False):
    """Save selected cases to local database."""
    input_cases = load_cases(input_file)
    
    if save_all:
        selected_cases = input_cases
    else:
        if not case_numbers:
            print("Error: No case numbers provided and --all not specified")
            sys.exit(1)
        
        normalized_targets = set(normalize_case_number(n) for n in case_numbers)
        selected_cases = []
        for case in input_cases:
            case_number = case.get("case_number", "") or case.get("案号", "") or case.get("id", "")
            normalized = normalize_case_number(case_number)
            if normalized in normalized_targets:
                selected_cases.append(case)
    
    print(f"Selected {len(selected_cases)} cases to save")
    
    existing_cases = load_local_database(db_path)
    print(f"Existing cases in local database: {len(existing_cases)}")
    
    existing_numbers = set()
    for case in existing_cases:
        case_number = case.get("case_number", "") or case.get("案号", "") or case.get("id", "")
        existing_numbers.add(normalize_case_number(case_number))
    
    new_cases = []
    duplicates = []
    txt_cases = []
    for case in selected_cases:
        case_number = case.get("case_number", "") or case.get("案号", "") or case.get("id", "")
        normalized = normalize_case_number(case_number)
        
        if normalized in existing_numbers:
            duplicates.append(case_number)
            if save_txt:
                txt_cases.append(case)
            continue
        
        case["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        case["source"] = case.get("source", "") or case.get("sources", ["manual"])
        new_cases.append(case)
        txt_cases.append(case)
        existing_numbers.add(normalized)
    
    all_cases = existing_cases + new_cases
    save_local_database(db_path, all_cases)
    
    if save_txt and txt_cases:
        txt_dir = db_path.parent
        txt_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nSaving cases as txt files to: {txt_dir}")
        for case in txt_cases:
            filepath = save_case_as_txt(case, txt_dir)
            print(f"  - {filepath.name}")
    
    print(f"\n=== Save Results ===")
    print(f"Total selected: {len(selected_cases)}")
    print(f"New cases saved: {len(new_cases)}")
    print(f"Duplicates skipped: {len(duplicates)}")
    print(f"Total in local database: {len(all_cases)}")
    
    if duplicates:
        print(f"\nSkipped duplicates:")
        for dup in duplicates[:5]:
            print(f"  - {dup}")
        if len(duplicates) > 5:
            print(f"  ... and {len(duplicates) - 5} more")
    
    if new_cases:
        print(f"\nNew cases added:")
        for case in new_cases[:5]:
            case_number = case.get("case_number", "") or case.get("案号", "") or "N/A"
            title = case.get("title", "") or case.get("标题", "") or "N/A"
            print(f"  - [{case_number}] {title[:40]}...")
        if len(new_cases) > 5:
            print(f"  ... and {len(new_cases) - 5} more")
    
    print(f"\nLocal database saved to: {db_path}")
    return len(new_cases)


def main():
    parser = argparse.ArgumentParser(description="Save cases to local database")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file (merged results)")
    parser.add_argument("--case-numbers", "-n", nargs="+", help="Case numbers to save")
    parser.add_argument("--all", action="store_true", help="Save all cases from input")
    parser.add_argument("--local-db", "-d", default="input/local/local_database.json",
                        help="Local database file path")
    parser.add_argument("--save-txt", action="store_true", help="Also save cases as txt files")
    args = parser.parse_args()
    
    if not args.all and not args.case_numbers:
        print("Error: Either --case-numbers or --all must be specified")
        parser.print_help()
        sys.exit(1)
    
    save_cases_to_local(args.input, args.case_numbers, Path(args.local_db), args.all, args.save_txt)


if __name__ == "__main__":
    main()