#!/usr/bin/env python3
"""View filtered cases by charge."""

import json
import argparse


def main():
    parser = argparse.ArgumentParser(description="View cases filtered by charge")
    parser.add_argument("--input", "-i", default="output/merged.json", help="Input JSON file")
    parser.add_argument("--charge", "-c", required=True, help="Charge to filter")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    cases = data.get("cases", data) if isinstance(data, dict) else data
    filtered = [c for c in cases if args.charge in (c.get("charge", "") or "")]

    print(f"=== {args.charge} — 类案检索结果 ===")
    print(f"共找到 {len(filtered)} 条案例")
    print()

    for i, c in enumerate(filtered, 1):
        print(f"【案例{i}】{c['case_number']}")
        print(f"   罪名：{c['charge']}")
        print(f"   量刑：{c['sentence']}")
        print(f"   数据量：{c['data_volume'] if c['data_volume'] else '未提及'}")
        print(f"   法院：{c['court']}")
        print(f"   审结日期：{c['verdict_date']}")
        if c.get("summary"):
            print(f"   案情摘要：{c['summary'][:100]}...")
        print()


if __name__ == "__main__":
    main()