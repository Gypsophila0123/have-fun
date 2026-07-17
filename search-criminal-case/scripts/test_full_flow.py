#!/usr/bin/env python3
"""
test_full_flow.py — 模拟完整用户交互流程测试脚本
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

CASE_TEXT = "2025年7月，黑客凌某利用某品牌智能摄像头固件中的未公开漏洞（CVE-2025-XXXX），编写自动化脚本批量扫描互联网，成功入侵超过8000台在线摄像头设备。凌某在这些设备中植入IRC控制木马，构建起庞大的物联网僵尸网络。同年9月，凌某受境外人员委托，将该僵尸网络租用给他人，对国内三家游戏公司的登录服务器发起持续72小时的分布式拒绝服务（DDoS）攻击，峰值流量达1.2Tbps，导致数百万玩家无法登录，游戏公司直接经济损失超400万元。攻击期间，凌某还通过加密聊天软件向受害公司发送勒索信息，要求支付比特币以停止攻击。警方通过分析攻击流量中的控制指令特征，溯源至境外跳板服务器，并最终在国内某住所抓获凌某，缴获其用于指挥攻击的手机和笔记本电脑，电子取证发现其保存有完整的设备入侵日志和攻击脚本。目前该案已侦查终结，移送检察机关审查起诉。"


def main():
    print("="*60)
    print("模拟完整用户交互流程测试")
    print("="*60)

    from main import (
        init_temp_dir, cleanup_temp_files,
        extract_case_elements, display_elements_with_highlights,
        correct_elements, save_extraction_feedback,
        detect_charges, ALL_CHARGES, run_command, generate_report
    )

    init_temp_dir()

    try:
        print("\n📋 案情摘要：")
        print(CASE_TEXT[:100] + "...")

        print("\n" + "="*60)
        print("Phase 1: 案情要素提取")
        print("="*60)
        elements = extract_case_elements(CASE_TEXT)
        missing_count = display_elements_with_highlights(elements)

        print("\n" + "-"*60)
        print("模拟用户修正要素")
        print("-"*60)

        corrections = {
            "target_system_type": "普通系统",
            "data_type": "系统控制权",
            "data_volume": "8000台设备",
            "consequence_severity": "特别严重",
            "defendant_role": "实行者",
            "subjective_intent": "直接故意",
            "special_circumstances": "跨境情节、勒索",
        }

        for key, value in corrections.items():
            if key in elements:
                print(f"  修改 {key}: {elements[key]} → {value}")
                elements[key] = value

        corrections_made = True

        print("\n" + "-"*60)
        print("保存反馈数据")
        print("-"*60)
        save_extraction_feedback(CASE_TEXT, elements, corrections_made)

        print("\n" + "="*60)
        print("Phase 2: 罪名发现")
        print("="*60)
        charges = detect_charges(CASE_TEXT)
        print(f"🎯 候选罪名：{', '.join(charges)}")

        print("\n" + "="*60)
        print("确认开始检索")
        print("="*60)

        from main import TEMP_DIR
        merged_file = TEMP_DIR / "merged.json"
        statistics_file = TEMP_DIR / "statistics.json"
        report_file = TEMP_DIR / "report.md"
        python_exe = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

        for charge in charges[:1]:
            print(f"\n{'#'*60}")
            print(f"处理罪名：{charge}")
            print(f"{'#'*60}")

            step1 = run_command(
                [str(python_exe), "scripts/merge_deduplicate.py",
                 "--input", "input/local/local_database.json",
                 "--output", str(merged_file)],
                "Step 1: 合并去重本地案例"
            )

            step2 = run_command(
                [str(python_exe), "scripts/case_statistics.py",
                 "--input", str(merged_file),
                 "--output", str(statistics_file),
                 "--charge", charge],
                f"Step 2: 按罪名「{charge}」统计分析"
            )

            if step1 and step2:
                print(f"\n📊 统计分析完成")
                generate_report(CASE_TEXT, charge, statistics_file, merged_file)

                step3 = run_command(
                    [str(python_exe), "scripts/generate_word.py",
                     "--input", str(report_file)],
                    "Step 3: 生成Word报告"
                )

                if step3:
                    from datetime import datetime
                    output_name = f"检索报告-{datetime.now().strftime('%Y-%m-%d')}.docx"
                    print(f"\n🎉 报告生成完成！")
                    print(f"📄 文件路径：{PROJECT_ROOT / 'output' / output_name}")

                    print(f"\n{'='*60}")
                    print("  检索流程已完成")
                    print(f"  报告文件：output/{output_name}")
                    print(f"  {'='*60}")

    finally:
        cleanup_temp_files()


if __name__ == "__main__":
    main()