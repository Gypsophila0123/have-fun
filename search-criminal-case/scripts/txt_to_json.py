#!/usr/bin/env python3
"""
txt_to_json.py — 将txt案例文件转换为JSON格式并入库

用法：
    python scripts/txt_to_json.py --input input/local --db input/local/local_database.json
"""

import argparse
import json
import os
import re
from pathlib import Path
from datetime import datetime


def parse_case_number(filename):
    """Extract case number from filename."""
    patterns = [
        r'(检例第[\d]+号)',
        r'([（(]\d{4}[）)]\w+刑初[\d]+号)',
        r'([（(]\d{4}[）)]\w+刑终[\d]+号)',
        r'([（(]\d{4}[）)]\w+刑初字第[\d]+号)',
    ]
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    return None


def parse_charge_from_filename(filename):
    """Extract charge from filename."""
    charge_map = {
        '侵入': '非法侵入计算机信息系统罪',
        '获取数据': '非法获取计算机信息系统数据罪',
        '非法控制': '非法控制计算机信息系统罪',
        '破坏': '破坏计算机信息系统罪',
        '提供程序工具': '提供侵入、非法控制计算机信息系统程序、工具罪',
    }
    for short, full in charge_map.items():
        if short in filename:
            return full
    return None


def parse_behavior_type(charge):
    """Map charge to behavior type."""
    if '侵入' in charge:
        return '侵入'
    elif '获取数据' in charge:
        return '获取数据'
    elif '非法控制' in charge and '提供' not in charge:
        return '非法控制'
    elif '破坏' in charge:
        return '破坏'
    elif '提供' in charge:
        return '提供程序工具'
    return '其他'


def extract_info_from_content(content):
    """Extract case information from content."""
    info = {}
    
    patterns = {
        'court': r'审理法院[：:]?\s*([^\n\r]+)',
        'verdict_date': r'审结日期[：:]?\s*([^\n\r]+)',
        'case_type': r'案件类型[：:]?\s*([^\n\r]+)',
        'procedure': r'审理程序[：:]?\s*([^\n\r]+)',
        'source': r'来源[：:]?\s*([^\n\r]+)',
        'defendants': r'被告人\s*([^\n，。；；]+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            info[key] = match.group(1).strip()
    
    sentence_patterns = [
        r'判处\s*(?:被告人\s*\w+\s*)?(有期徒刑[^\n\r；。]+)',
        r'（\d+）\s*被告人\s*\w+\s*犯\s*[^，。；]+，\s*(有期徒刑[^\n\r；。]+)',
    ]
    for pattern in sentence_patterns:
        sentence_match = re.search(pattern, content)
        if sentence_match:
            sentence_text = sentence_match.group(1).strip()
            if len(sentence_text) > 4 and '条' not in sentence_text:
                info['sentence'] = sentence_text
                break
    
    penalty_match = re.search(r'刑罚[：:]?\s*([^\n\r]+)', content)
    if penalty_match and not info.get('sentence'):
        penalty_text = penalty_match.group(1).strip()
        sent_match = re.search(r'(有期徒刑[^\n\r；。]+)', penalty_text)
        if sent_match:
            info['sentence'] = sent_match.group(1).strip()
    
    data_volume_patterns = [
        r'(提取到\s*\d+\s*条[^，。\n\r]*)',
        r'(非法增加[^，。\n\r]*\d+\s*条[^，。\n\r]*)',
        r'(\d+\s*条数据)',
        r'(\d+[万余]?\s*条数据)',
        r'(\d+\s*台[^，。\n\r]*计算机)',
        r'(\d+\s*GB[^，。\n\r]*)',
        r'(\d+\s*组[^，。\n\r]*数据)',
    ]
    for pattern in data_volume_patterns:
        data_match = re.search(pattern, content)
        if data_match:
            data_text = data_match.group(1).strip()
            if '第1款' not in data_text and '第2款' not in data_text and '条第' not in data_text:
                info['data_volume'] = data_text
                break
    
    summary_match = re.search(r'【基本案情】\s*([^【]+)', content, re.DOTALL)
    if summary_match:
        info['summary'] = summary_match.group(1).strip()[:500]
    
    return info


def txt_to_json(input_dir, db_path):
    """Convert txt files to JSON and import to database."""
    input_path = Path(input_dir)
    txt_files = sorted(input_path.glob('*.txt'))
    
    db_path = Path(db_path)
    if db_path.exists():
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                db_data = json.load(f)
            existing_cases = db_data.get('cases', [])
        except:
            existing_cases = []
    else:
        existing_cases = []
    
    existing_numbers = set()
    for case in existing_cases:
        case_number = case.get('case_number', '')
        charge = case.get('charge', '')
        key = f"{case_number}_{charge}"
        existing_numbers.add(key)
    
    new_cases = []
    skipped = 0
    
    for txt_file in txt_files:
        case_number = parse_case_number(txt_file.name)
        charge = parse_charge_from_filename(txt_file.name)
        
        if not case_number:
            case_number = txt_file.stem.replace('_', '-')
        
        if not charge:
            print(f"  Warning: No charge found in {txt_file.name}")
            continue
        
        key = f"{case_number}_{charge}"
        if key in existing_numbers:
            print(f"  Skipping duplicate: {txt_file.name}")
            skipped += 1
            continue
        
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  Error reading {txt_file.name}: {e}")
            continue
        
        info = extract_info_from_content(content)
        
        case_data = {
            'case_number': case_number,
            'title': f"{case_number} {charge}",
            'document_type': info.get('case_type', '刑事判决书'),
            'sentence': info.get('sentence', ''),
            'data_volume': info.get('data_volume', ''),
            'behavior_type': parse_behavior_type(charge),
            'charge': charge,
            'priority': 'guiding' if '检例' in case_number or '指导案例' in case_number else 'normal',
            'court_level': '基层人民法院' if '区' in info.get('court', '') else '中级人民法院',
            'court': info.get('court', ''),
            'verdict_date': info.get('verdict_date', ''),
            'source': info.get('source', '中国裁判文书网'),
            'summary': info.get('summary', ''),
            'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        new_cases.append(case_data)
        existing_numbers.add(key)
        print(f"  Imported: {txt_file.name}")
    
    all_cases = existing_cases + new_cases
    
    db_data = {
        'cases': all_cases,
        'metadata': {
            'version': '1.0',
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_cases': len(all_cases)
        }
    }
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"Total txt files found: {len(txt_files)}")
    print(f"New cases imported: {len(new_cases)}")
    print(f"Duplicates skipped: {skipped}")
    print(f"Total cases in database: {len(all_cases)}")


def main():
    parser = argparse.ArgumentParser(description="Convert txt case files to JSON and import to database")
    parser.add_argument("--input", "-i", default="input/local", help="Input directory")
    parser.add_argument("--db", "-d", default="input/local/local_database.json", help="Database file path")
    args = parser.parse_args()
    
    txt_to_json(args.input, args.db)


if __name__ == "__main__":
    main()