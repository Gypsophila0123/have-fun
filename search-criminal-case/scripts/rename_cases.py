#!/usr/bin/env python3
"""
rename_cases.py — 案例文件重命名工具

用途：将 input/local/ 下的 txt 案例文件统一重命名为"案号+核心罪名"格式

用法：
    python scripts/rename_cases.py --input input/local --output input/local
"""

import argparse
import os
import re
from pathlib import Path


def extract_case_number(content):
    """Extract case number from document content."""
    patterns = [
        r'案\s*号\s*[：:]?\s*([^\n\r]+)',
        r'案件编号\s*[：:]?\s*([^\n\r]+)',
        r'(检例第[\d]+号)',
        r'(指导案例[\d]+号)',
        r'([（(]\d{4}[）)]\w+刑初[\d]+号)',
        r'([（(]\d{4}[）)]\w+刑终[\d]+号)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
    return None


def extract_main_charges(content):
    """Extract main charges from document content."""
    target_charges = [
        ('非法侵入计算机信息系统罪', '侵入'),
        ('非法获取计算机信息系统数据罪', '获取数据'),
        ('非法控制计算机信息系统罪', '非法控制'),
        ('破坏计算机信息系统罪', '破坏'),
        ('提供侵入、非法控制计算机信息系统程序、工具罪', '提供程序工具'),
    ]
    
    charges_found = []
    for full_name, short_name in target_charges:
        if full_name in content:
            charges_found.append((full_name, short_name))
    
    if not charges_found:
        return []
    
    return charges_found


def clean_filename(filename):
    """Clean filename by removing illegal characters."""
    illegal_chars = r'[\\/:*?"<>|]'
    cleaned = re.sub(illegal_chars, '', filename)
    cleaned = cleaned.replace(' ', '')
    return cleaned


def rename_files(input_dir, output_dir):
    """Rename case files to 'case_number + charge' format."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    txt_files = sorted(input_path.glob('*.txt'))
    renamed_count = 0
    split_count = 0
    
    for txt_file in txt_files:
        if txt_file.name.startswith('检例') or txt_file.name.startswith('(20') or txt_file.name.startswith('（20'):
            print(f"Skipping already named file: {txt_file.name}")
            continue
        
        print(f"\nProcessing: {txt_file.name}")
        
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  Error reading file: {e}")
            continue
        
        case_number = extract_case_number(content)
        if not case_number:
            print(f"  Warning: No case number found, skipping")
            continue
        
        charges = extract_main_charges(content)
        if not charges:
            print(f"  Warning: No target charges found, skipping")
            continue
        
        print(f"  Case number: {case_number}")
        print(f"  Charges found: {[c[0] for c in charges]}")
        
        if len(charges) == 1:
            full_name, short_name = charges[0]
            new_filename = f"{case_number}_{short_name}.txt"
            new_filename = clean_filename(new_filename)
            new_path = output_path / new_filename
            
            if new_path.exists():
                print(f"  Warning: {new_filename} already exists")
                continue
            
            os.rename(txt_file, new_path)
            print(f"  Renamed to: {new_filename}")
            renamed_count += 1
        else:
            for i, (full_name, short_name) in enumerate(charges):
                new_filename = f"{case_number}_{short_name}_{i+1}.txt"
                new_filename = clean_filename(new_filename)
                new_path = output_path / new_filename
                
                if new_path.exists():
                    print(f"  Warning: {new_filename} already exists")
                    continue
                
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"  Split to: {new_filename}")
                split_count += 1
            
            os.remove(txt_file)
            print(f"  Original file removed after splitting")
    
    print(f"\n=== Summary ===")
    print(f"Total files processed: {len(txt_files)}")
    print(f"Files renamed: {renamed_count}")
    print(f"Files split: {split_count}")


def main():
    parser = argparse.ArgumentParser(description="Rename case files to 'case_number + charge' format")
    parser.add_argument("--input", "-i", default="input/local", help="Input directory")
    parser.add_argument("--output", "-o", default="input/local", help="Output directory")
    args = parser.parse_args()
    
    rename_files(args.input, args.output)


if __name__ == "__main__":
    main()