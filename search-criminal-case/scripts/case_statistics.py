#!/usr/bin/env python3
"""
case_statistics.py — 类案分组统计与定量分析工具

用途：Phase 3 对去重后的类案结果进行六维度分组统计和量刑分布分析
依赖：无外部依赖（纯标准库）

用法：
    python case_statistics.py --input merged.json --output statistics.json
"""

import argparse
import json
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path


def chinese_to_arabic(chinese_num):
    """Convert Chinese numbers to Arabic numbers."""
    chinese_digits = {'零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
                      '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    units = {'十': 10, '百': 100, '千': 1000, '万': 10000}

    result = 0
    temp = 0

    for char in chinese_num:
        if char in chinese_digits:
            temp = chinese_digits[char]
        elif char in units:
            unit = units[char]
            if temp == 0:
                temp = 1
            result += temp * unit
            temp = 0
        else:
            try:
                temp = int(char)
            except ValueError:
                pass

    result += temp
    return result if result > 0 else temp


def extract_sentence_months(sentence_text):
    """Extract sentence length in months from text."""
    if not sentence_text:
        return None

    text = str(sentence_text)

    # Check for probation / exemption
    if "免予" in text or "免于" in text or "免除" in text:
        return 0  # Exemption = 0 months
    if "无罪" in text:
        return -1  # Not guilty

    year_pattern = r"有期徒刑\s*([零一二两三四五六七八九十\d]+)\s*年"
    month_pattern = r"有期徒刑\s*([零一二两三四五六七八九十\d]+)\s*个月"
    detention_pattern = r"拘役\s*([零一二两三四五六七八九十\d]+)\s*(?:个月|日)"

    year_match = re.search(year_pattern, text)
    month_match = re.search(month_pattern, text)
    detention_match = re.search(detention_pattern, text)

    total_months = 0
    if year_match:
        year_num = chinese_to_arabic(year_match.group(1))
        total_months += year_num * 12
    if month_match:
        month_num = chinese_to_arabic(month_match.group(1))
        total_months += month_num
    if detention_match and not year_match:
        detention_num = chinese_to_arabic(detention_match.group(1))
        total_months += detention_num

    probation_pattern = r"缓刑\s*([零一二两三四五六七八九十\d]+)"
    probation_match = re.search(probation_pattern, text)
    if probation_match and not year_match and not month_match:
        return None  # Probation without main sentence

    if total_months > 0:
        return total_months
    if "缓刑" in text:
        return 0  # Treat probation as 0 for grouping (separate group)

    return None


def categorize_sentence(months, has_probation):
    """Categorize sentence into sentencing tier."""
    if months is None:
        return "未知"
    if months == -1:
        return "无罪"
    if months == 0 and has_probation:
        return "缓刑"
    if months == 0:
        return "免刑"
    if months <= 12:
        return "≤1年"
    if months <= 36:
        return "1-3年"
    if months <= 60:
        return "3-5年"
    if months > 60:
        return "5年以上"
    return "未知"


def extract_data_volume(text):
    """Extract data volume from text."""
    if not text:
        return None
    text = str(text)

    # Try to find numbers followed by 条/组/份
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(万)?\s*(条|组|份|个)", text)
    if matches:
        num = float(matches[0][0])
        if matches[0][1] == "万":
            num *= 10000
        return int(num)
    return None


def categorize_data_volume(volume):
    """Categorize data volume."""
    if volume is None:
        return "未知"
    if volume < 10000:
        return "<1万条"
    if volume < 50000:
        return "1-5万条"
    if volume < 100000:
        return "5-10万条"
    if volume < 500000:
        return "10-50万条"
    return ">50万条"


def extract_economic_loss(text):
    """Extract economic loss amount."""
    if not text:
        return None
    text = str(text)
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(万)?\s*元", text)
    if matches:
        num = float(matches[0][0])
        if matches[0][1] == "万":
            num *= 10000
        return num
    return None


def categorize_economic_loss(amount):
    """Categorize economic loss."""
    if amount is None:
        return "未知"
    if amount < 10000:
        return "<1万"
    if amount < 50000:
        return "1-5万"
    if amount < 200000:
        return "5-20万"
    if amount < 500000:
        return "20-50万"
    return ">50万"


def extract_mitigating_factors(case):
    """Extract mitigating circumstances."""
    factors = []
    text = " ".join(str(v) for v in case.values() if v)

    factor_map = {
        "自首": ["自首"],
        "坦白": ["坦白"],
        "立功": ["立功"],
        "退赔退缴": ["退赔", "退缴", "退回"],
        "认罪认罚": ["认罪认罚"],
        "初犯": ["初犯", "偶犯"],
    }

    for factor, keywords in factor_map.items():
        if any(kw in text for kw in keywords):
            factors.append(factor)

    return factors


def extract_aggravating_factors(case):
    """Extract aggravating circumstances."""
    factors = []
    text = " ".join(str(v) for v in case.values() if v)

    factor_map = {
        "累犯": ["累犯"],
        "前科": ["前科"],
        "组织者": ["组织", "首要"],
        "跨境犯罪": ["跨境", "境外"],
    }

    for factor, keywords in factor_map.items():
        if any(kw in text for kw in keywords):
            factors.append(factor)

    return factors


def compute_statistics(cases):
    """Compute full statistics for the case list."""
    stats = {
        "overview": {
            "total_cases": len(cases),
            "guiding_cases": sum(1 for c in cases if c.get("priority") == "guiding"),
            "typical_cases": sum(1 for c in cases if c.get("priority") == "typical"),
        },
        "sentencing_distribution": {},
        "behavior_type_distribution": {},
        "data_volume_distribution": {},
        "economic_loss_distribution": {},
        "mitigating_factors_distribution": {},
        "aggravating_factors_distribution": {},
        "probation_rate": 0,
        "cross_analysis": {},
    }

    if not cases:
        return stats

    # Sentencing distribution
    sentence_groups = defaultdict(list)
    for case in cases:
        sentence_text = case.get("sentence", "") or case.get("量刑", "") or case.get("verdict", "")
        has_probation = "缓刑" in str(sentence_text)
        months = extract_sentence_months(sentence_text)
        tier = categorize_sentence(months, has_probation)
        sentence_groups[tier].append(case)

    for tier, tier_cases in sentence_groups.items():
        stats["sentencing_distribution"][tier] = {
            "count": len(tier_cases),
            "percentage": round(len(tier_cases) / len(cases) * 100, 1),
            "example_case_numbers": [c.get("case_number", "") or c.get("案号", "") for c in tier_cases[:3]],
        }

    # Behavior type distribution
    for case in cases:
        behavior = case.get("behavior_type", "") or case.get("行为类型", "") or "未知"
        if behavior not in stats["behavior_type_distribution"]:
            stats["behavior_type_distribution"][behavior] = {"count": 0, "percentage": 0}
        stats["behavior_type_distribution"][behavior]["count"] += 1

    for behavior, data in stats["behavior_type_distribution"].items():
        data["percentage"] = round(data["count"] / len(cases) * 100, 1)

    # Data volume distribution
    volume_groups = defaultdict(list)
    for case in cases:
        text = " ".join(str(v) for v in case.values() if v)
        volume = extract_data_volume(text)
        tier = categorize_data_volume(volume)
        volume_groups[tier].append(case)

    for tier, tier_cases in volume_groups.items():
        stats["data_volume_distribution"][tier] = {
            "count": len(tier_cases),
            "percentage": round(len(tier_cases) / len(cases) * 100, 1),
        }

    # Economic loss distribution
    loss_groups = defaultdict(list)
    for case in cases:
        text = " ".join(str(v) for v in case.values() if v)
        amount = extract_economic_loss(text)
        tier = categorize_economic_loss(amount)
        loss_groups[tier].append(case)

    for tier, tier_cases in loss_groups.items():
        stats["economic_loss_distribution"][tier] = {
            "count": len(tier_cases),
            "percentage": round(len(tier_cases) / len(cases) * 100, 1),
        }

    # Mitigating factors
    mitigating_counter = Counter()
    for case in cases:
        factors = extract_mitigating_factors(case)
        for f in factors:
            mitigating_counter[f] += 1

    for factor, count in mitigating_counter.most_common():
        stats["mitigating_factors_distribution"][factor] = {
            "count": count,
            "percentage": round(count / len(cases) * 100, 1),
        }

    # Aggravating factors
    aggravating_counter = Counter()
    for case in cases:
        factors = extract_aggravating_factors(case)
        for f in factors:
            aggravating_counter[f] += 1

    for factor, count in aggravating_counter.most_common():
        stats["aggravating_factors_distribution"][factor] = {
            "count": count,
            "percentage": round(count / len(cases) * 100, 1),
        }

    # Probation rate
    probation_count = sum(1 for c in cases if "缓刑" in str(c.get("sentence", "") or c.get("量刑", "") or c.get("verdict", "")))
    stats["probation_rate"] = round(probation_count / len(cases) * 100, 1) if cases else 0

    # Cross analysis: behavior type x sentencing
    cross = defaultdict(lambda: defaultdict(int))
    for case in cases:
        behavior = case.get("behavior_type", "") or case.get("行为类型", "") or "未知"
        sentence_text = case.get("sentence", "") or case.get("量刑", "") or case.get("verdict", "")
        has_probation = "缓刑" in str(sentence_text)
        months = extract_sentence_months(sentence_text)
        tier = categorize_sentence(months, has_probation)
        cross[behavior][tier] += 1

    stats["cross_analysis"]["behavior_x_sentencing"] = {
        behavior: dict(tiers) for behavior, tiers in cross.items()
    }

    return stats


def main():
    parser = argparse.ArgumentParser(description="Compute case statistics from merged results")
    parser.add_argument("--input", "-i", required=True, help="Input merged JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output statistics JSON file")
    parser.add_argument("--charge", "-c", help="Filter cases by charge (only count cases matching this charge)")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data.get("cases", data) if isinstance(data, dict) else data

    if args.charge:
        filtered_cases = []
        for case in cases:
            case_charge = case.get("charge", "") or case.get("罪名", "") or case.get("判定罪名", "") or ""
            if args.charge in case_charge or case_charge in args.charge:
                filtered_cases.append(case)
        print(f"Filtered to {len(filtered_cases)} cases matching charge: {args.charge}")
        cases = filtered_cases

    print(f"Computing statistics for {len(cases)} cases...")
    stats = compute_statistics(cases)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\nStatistics summary:")
    print(f"  Total cases: {stats['overview']['total_cases']}")
    print(f"  Guiding cases: {stats['overview']['guiding_cases']}")
    print(f"  Probation rate: {stats['probation_rate']}%")
    print(f"\nSentencing distribution:")
    for tier, data in stats["sentencing_distribution"].items():
        print(f"  {tier}: {data['count']} ({data['percentage']}%)")

    print(f"\nStatistics saved to: {output_path}")


if __name__ == "__main__":
    main()
