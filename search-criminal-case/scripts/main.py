#!/usr/bin/env python3
"""
main.py — 计算机犯罪类案检索系统交互式终端入口

用法：
    python scripts/main.py                              # 交互式模式
    python scripts/main.py --charge "罪名"              # 指定罪名快速模式
    python scripts/main.py --help                       # 显示帮助

示例：
    python scripts/main.py --charge "非法控制计算机信息系统罪"
"""

import argparse
import json
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent

CHARGE_KEYWORDS = {
    "非法侵入计算机信息系统罪": ["侵入", "进入", "登录", "破解密码"],
    "非法获取计算机信息系统数据罪": ["获取", "下载", "复制", "窃取", "数据"],
    "非法控制计算机信息系统罪": ["控制", "操控", "后门", "权限", "Root"],
    "破坏计算机信息系统罪": ["破坏", "删除", "修改", "加密", "瘫痪", "病毒"],
    "提供侵入、非法控制计算机信息系统程序、工具罪": ["提供", "制作", "传播", "程序", "工具"],
}

ALL_CHARGES = list(CHARGE_KEYWORDS.keys())


def detect_charges(case_text):
    """基于关键词匹配发现候选罪名（简化版，仅供终端测试）"""
    matched = []
    for charge, keywords in CHARGE_KEYWORDS.items():
        for kw in keywords:
            if kw in case_text:
                matched.append(charge)
                break
    return matched


ELEMENT_DEFINITIONS = {
    "case_summary": {"label": "案情概述", "description": "一句话案情概述", "max_length": 200},
    "behavior_type": {"label": "行为类型", "description": "侵入/获取数据/非法控制/提供程序工具/破坏系统/组合行为", 
                      "options": ["侵入", "获取数据", "非法控制", "提供程序工具", "破坏系统", "组合行为"]},
    "target_system_type": {"label": "目标系统类型", "description": "国家事务/国防建设/尖端科技/其他重要领域/普通系统",
                           "options": ["国家事务", "国防建设", "尖端科技", "其他重要领域", "普通系统"]},
    "target_system_detail": {"label": "系统具体描述", "description": "如某省政府门户网站、某银行系统等"},
    "method": {"label": "技术手段", "description": "如SQL注入、暴力破解、木马植入等"},
    "data_type": {"label": "数据类型", "description": "个人信息/账号密码/金融数据/系统控制权/程序工具/不涉及",
                  "options": ["个人信息", "账号密码", "金融数据", "系统控制权", "程序工具", "不涉及"]},
    "data_volume": {"label": "数据量", "description": "条数/金额/数量，如：10000条、5万元"},
    "consequence": {"label": "后果", "description": "系统瘫痪/数据泄露/经济损失/未造成严重后果/其他",
                    "options": ["系统瘫痪", "数据泄露", "经济损失", "未造成严重后果", "其他"]},
    "consequence_severity": {"label": "后果严重程度", "description": "严重/特别严重/未提及",
                             "options": ["严重", "特别严重", "未提及"]},
    "economic_loss": {"label": "经济损失", "description": "具体经济损失金额，如：50万元"},
    "defendant_role": {"label": "被告人角色", "description": "实行者/组织者/帮助者/提供者",
                       "options": ["实行者", "组织者", "帮助者", "提供者"]},
    "subjective_intent": {"label": "主观故意", "description": "直接故意/间接故意/过失",
                          "options": ["直接故意", "间接故意", "过失"]},
    "special_circumstances": {"label": "特殊情节", "description": "如未成年人/累犯/共同犯罪/退赔退缴等"},
}


def extract_case_elements(case_text):
    """从案情文本中提取结构化要素"""
    elements = {}
    
    for key, config in ELEMENT_DEFINITIONS.items():
        if key == "case_summary":
            elements[key] = case_text[:200].strip() if case_text else "未提及"
        elif key == "behavior_type":
            text = case_text or ""
            if any(k in text for k in ["侵入", "进入", "登录", "破解"]):
                elements[key] = "侵入"
            elif any(k in text for k in ["获取", "下载", "复制", "窃取", "数据"]):
                elements[key] = "获取数据"
            elif any(k in text for k in ["控制", "操控", "后门", "权限"]):
                elements[key] = "非法控制"
            elif any(k in text for k in ["破坏", "删除", "修改", "加密", "瘫痪"]):
                elements[key] = "破坏系统"
            elif any(k in text for k in ["提供", "制作", "传播", "程序", "工具"]):
                elements[key] = "提供程序工具"
            elif len(text) > 0:
                elements[key] = "组合行为"
            else:
                elements[key] = "未提及"
        elif key == "target_system_type":
            text = case_text or ""
            if any(k in text for k in ["国家", "政府", "行政"]):
                elements[key] = "国家事务"
            elif any(k in text for k in ["国防", "军队", "军事"]):
                elements[key] = "国防建设"
            elif any(k in text for k in ["科技", "科研", "尖端"]):
                elements[key] = "尖端科技"
            elif any(k in text for k in ["银行", "金融", "医疗", "通信"]):
                elements[key] = "其他重要领域"
            else:
                elements[key] = "未提及"
        elif key == "target_system_detail":
            text = case_text or ""
            system_keywords = ["系统", "平台", "网站", "数据库", "服务器"]
            for kw in system_keywords:
                idx = text.find(kw)
                if idx != -1:
                    start = max(0, idx - 30)
                    end = min(len(text), idx + 10)
                    elements[key] = text[start:end].strip()
                    break
            else:
                elements[key] = "未提及"
        elif key == "method":
            text = case_text or ""
            method_keywords = [("SQL注入", ["SQL注入"]), ("暴力破解", ["暴力破解", "暴力攻击"]),
                               ("木马植入", ["木马", "病毒", "植入"]), ("钓鱼", ["钓鱼"]),
                               ("社工", ["社工"]), ("数据爬取", ["爬取", "爬虫"])]
            for name, kws in method_keywords:
                if any(kw in text for kw in kws):
                    elements[key] = name
                    break
            else:
                elements[key] = "未提及"
        elif key == "data_type":
            text = case_text or ""
            if any(k in text for k in ["个人信息", "身份信息", "隐私"]):
                elements[key] = "个人信息"
            elif any(k in text for k in ["账号", "密码", "登录"]):
                elements[key] = "账号密码"
            elif any(k in text for k in ["金融", "资金", "银行"]):
                elements[key] = "金融数据"
            elif any(k in text for k in ["控制", "权限", "后门"]):
                elements[key] = "系统控制权"
            else:
                elements[key] = "未提及"
        elif key == "data_volume":
            import re
            text = case_text or ""
            matches = re.findall(r"(\d+(?:\.\d+)?)\s*(万)?\s*(条|组|份|个|条记录)", text)
            if matches:
                num = float(matches[0][0])
                unit = matches[0][1] or ""
                measure = matches[0][2]
                elements[key] = f"{num}{unit}{measure}"
            else:
                elements[key] = "未提及"
        elif key == "consequence":
            text = case_text or ""
            if any(k in text for k in ["瘫痪", "崩溃", "无法"]):
                elements[key] = "系统瘫痪"
            elif any(k in text for k in ["泄露", "泄露", "外流"]):
                elements[key] = "数据泄露"
            elif any(k in text for k in ["损失", "亏损", "金额"]):
                elements[key] = "经济损失"
            else:
                elements[key] = "未提及"
        elif key == "economic_loss":
            import re
            text = case_text or ""
            matches = re.findall(r"(\d+(?:\.\d+)?)\s*(万)?\s*元", text)
            if matches:
                num = float(matches[0][0])
                unit = matches[0][1] or ""
                elements[key] = f"{num}{unit}元"
            else:
                elements[key] = "未提及"
        else:
            elements[key] = "未提及"
    
    return elements


def display_elements_with_highlights(elements):
    """高亮显示未提及字段的要素表"""
    print("\n" + "="*60)
    print("📋 案情要素提取结果")
    print("="*60)
    
    missing_count = 0
    for key, config in ELEMENT_DEFINITIONS.items():
        value = elements.get(key, "未提及")
        if value == "未提及":
            print(f"  ⚠️ {config['label']}: {value}")
            print(f"     提示: {config['description']}")
            if "options" in config:
                print(f"     可选值: {', '.join(config['options'])}")
            missing_count += 1
        else:
            print(f"  ✓ {config['label']}: {value}")
    
    if missing_count > 0:
        print(f"\n⚠️ 共有 {missing_count} 个字段未提取到，请在修正环节补充。")
    else:
        print("\n✓ 所有要素已提取完成")
    
    return missing_count


def correct_elements(elements):
    """交互式修正要素"""
    while True:
        print("\n" + "-"*60)
        print("要素修正模式")
        print("-"*60)
        print("请输入要修改的字段序号（输入 'q' 退出修正，输入 'r' 重置所有）：")
        
        keys = list(ELEMENT_DEFINITIONS.keys())
        for i, key in enumerate(keys, 1):
            config = ELEMENT_DEFINITIONS[key]
            value = elements.get(key, "未提及")
            status = "⚠️" if value == "未提及" else "✓"
            print(f"  {i}. {status} {config['label']}: {value}")
        
        choice = input("\n请选择：").strip()
        
        if choice.lower() == 'q':
            break
        elif choice.lower() == 'r':
            confirm = input("确定要重置所有要素吗？(y/N) ").strip().lower()
            if confirm == 'y':
                for key in keys:
                    elements[key] = "未提及"
                print("已重置所有要素")
            continue
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                key = keys[idx]
                config = ELEMENT_DEFINITIONS[key]
                print(f"\n修改 {config['label']}:")
                print(f"当前值: {elements.get(key, '未提及')}")
                print(f"说明: {config['description']}")
                
                if "options" in config:
                    print("可选值:")
                    for j, opt in enumerate(config["options"], 1):
                        print(f"  {j}. {opt}")
                    sub_choice = input("请输入序号或直接输入新值：").strip()
                    try:
                        sub_idx = int(sub_choice) - 1
                        if 0 <= sub_idx < len(config["options"]):
                            elements[key] = config["options"][sub_idx]
                        else:
                            elements[key] = sub_choice
                    except ValueError:
                        elements[key] = sub_choice
                else:
                    new_value = input("请输入新值：").strip()
                    elements[key] = new_value if new_value else "未提及"
                
                print(f"✓ 已修改为: {elements[key]}")
            else:
                print("无效的序号")
        except ValueError:
            print("请输入有效的序号")
    
    return elements


FEEDBACK_DIR = PROJECT_ROOT / "input" / "training_data"

def save_extraction_feedback(case_text, elements, corrections_made):
    """保存提取反馈数据"""
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    
    feedback = {
        "case_text": case_text,
        "extracted_elements": elements,
        "corrections_made": corrections_made,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "feedback_type": "correction" if corrections_made else "confirmation"
    }
    
    filename = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = FEEDBACK_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(feedback, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 反馈数据已保存: {filepath.name}")
    return filepath


TEMP_DIR = PROJECT_ROOT / "output" / "temp"

def init_temp_dir():
    """初始化临时目录，清理残留文件"""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    cleaned = 0
    for f in TEMP_DIR.glob("*"):
        try:
            f.unlink()
            cleaned += 1
        except Exception as e:
            print(f"⚠️ 清理残留临时文件失败：{f} - {e}")
    
    if cleaned > 0:
        print(f"\n✓ 清理了 {cleaned} 个残留临时文件")

def cleanup_temp_files():
    """清理临时文件（包含 temp 目录）"""
    temp_patterns = [
        TEMP_DIR / "merged.json",
        TEMP_DIR / "statistics.json",
        TEMP_DIR / "statistics_data.json",
        TEMP_DIR / "statistics_tool.json",
        TEMP_DIR / "report.md",
        PROJECT_ROOT / "input" / "semantic" / "mcp_results.json",
    ]
    
    cleaned = 0
    for f in temp_patterns:
        if f.exists():
            try:
                f.unlink()
                cleaned += 1
            except Exception as e:
                print(f"⚠️ 清理失败：{f} - {e}")
    
    if TEMP_DIR.exists():
        try:
            TEMP_DIR.rmdir()
            cleaned += 1
        except Exception:
            pass
    
    if cleaned > 0:
        print(f"\n✓ 已清理 {cleaned} 个临时文件")
    return cleaned


def run_command(cmd, description=""):
    """运行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"执行：{description}")
    print(f"命令：{' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding="utf-8", 
            errors="replace",
            cwd=PROJECT_ROOT
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"警告：{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"执行失败：{e}")
        return False


def generate_report(case_text, charge, statistics_file, merged_file):
    """生成Markdown报告"""
    report_path = TEMP_DIR / "report.md"
    
    with open(statistics_file, "r", encoding="utf-8") as f:
        stats = json.load(f)
    
    with open(merged_file, "r", encoding="utf-8") as f:
        merged_data = json.load(f)
    cases = merged_data.get("cases", [])
    filtered_cases = [c for c in cases if charge in (c.get("charge", "") or "")]
    
    report_content = f"""# 计算机犯罪类案检索报告

**检索日期**：{datetime.now().strftime("%Y年%m月%d日")}
**检索罪名**：{charge}
**检索模式**：纯本地模式

> ⚠️ **风险提醒**：本报告由系统自动生成，基于本地案例库检索结果，仅供参考，不构成任何法律意见或建议。具体案件请咨询专业律师。

---

## 一、案件概述

### 1.1 基本案情

{case_text}

---

## 二、罪名分析

### 2.1 锚定罪名

{charge}

### 2.2 法条依据

《中华人民共和国刑法》第二百八十五条或第二百八十六条

---

## 三、类案检索说明

**检索模式**：纯本地模式（北大法宝MCP未连接）
**数据源**：本地案例库

---

## 四、类案统计分析

### 4.1 案件总览

| 指标 | 数值 |
|------|------|
| 匹配案例数 | {stats["overview"]["total_cases"]} |
| 指导性案例 | {stats["overview"]["guiding_cases"]} |
| 缓刑率 | {stats["probation_rate"]}% |

### 4.2 量刑分布

| 量刑档次 | 案件数 | 占比 |
|----------|--------|------|
"""
    
    for tier, data in stats["sentencing_distribution"].items():
        report_content += f"| {tier} | {data['count']} | {data['percentage']}% |\n"
    
    report_content += "\n### 4.3 典型案例\n\n"
    
    for i, c in enumerate(filtered_cases[:5], 1):
        report_content += f"#### {i}. {c['case_number']}\n"
        report_content += f"- 罪名：{c['charge']}\n"
        report_content += f"- 量刑：{c['sentence']}\n"
        report_content += f"- 法院：{c['court']}\n"
        if c.get("summary"):
            report_content += f"- 案情：{c['summary'][:150]}...\n"
        report_content += "\n"
    
    report_content += f"""---

## 五、风险提示

⚠️ 本报告仅供参考，不构成任何法律意见或建议。实际案件处理需咨询专业律师。

**报告生成时间**：{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}
"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"\n✓ 报告模板已生成：{report_path}")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="计算机犯罪类案检索系统终端入口")
    parser.add_argument("--charge", "-c", help="指定罪名（跳过自动发现）")
    parser.add_argument("--case", "-k", help="案情文本（直接输入）")
    args = parser.parse_args()
    
    print("="*60)
    print("  计算机犯罪类案检索系统")
    print("="*60)
    
    init_temp_dir()
    
    try:
        if args.case:
            case_text = args.case
        else:
            print("\n请输入案情描述：")
            print("（输入完成后，请单独输入一行 END 并按 Enter 结束）")
            print("-"*40)
            case_text = []
            while True:
                try:
                    line = input()
                    if line.strip().upper() == "END":
                        break
                    case_text.append(line)
                except EOFError:
                    break
            case_text = "\n".join(case_text)
        
        if not case_text.strip():
            print("❌ 案情不能为空")
            return
        
        print(f"\n📋 案情摘要：{case_text[:100]}...")
        
        print("\n" + "="*60)
        print("Phase 1: 案情要素提取")
        print("="*60)
        elements = extract_case_elements(case_text)
        missing_count = display_elements_with_highlights(elements)
        
        corrections_made = False
        
        if missing_count > 0:
            choice = input("\n是否需要修正要素？(y/N) ").strip().lower()
            if choice == 'y':
                original_elements = elements.copy()
                elements = correct_elements(elements)
                corrections_made = original_elements != elements
        else:
            choice = input("\n要素提取完整，是否需要修正？(y/N) ").strip().lower()
            if choice == 'y':
                original_elements = elements.copy()
                elements = correct_elements(elements)
                corrections_made = original_elements != elements
        
        save_feedback = input("\n是否保存提取反馈数据（用于模型迭代）？(y/N) ").strip().lower()
        if save_feedback == 'y':
            save_extraction_feedback(case_text, elements, corrections_made)
        
        if args.charge:
            charges = [args.charge]
        else:
            charges = detect_charges(case_text)
            if not charges:
                print("\n⚠️ 未自动识别到罪名，请手动选择：")
                for i, c in enumerate(ALL_CHARGES, 1):
                    print(f"  {i}. {c}")
                while True:
                    try:
                        choice = int(input("请输入罪名序号："))
                        if 1 <= choice <= len(ALL_CHARGES):
                            charges = [ALL_CHARGES[choice-1]]
                            break
                        print("请输入有效序号")
                    except ValueError:
                        print("请输入数字")
        
        print(f"\n🎯 候选罪名：{', '.join(charges)}")
        
        if args.case:
            confirm = "y"
            print("\n（快速模式：自动确认）")
        else:
            confirm = input("\n确认开始检索？(y/N) ").strip().lower()
            if confirm != "y":
                print("已取消")
                return
        
        print("\n🔍 开始检索...")
        
        merged_file = TEMP_DIR / "merged.json"
        statistics_file = TEMP_DIR / "statistics.json"
        report_file = TEMP_DIR / "report.md"
        
        python_exe = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
        
        if not python_exe.exists():
            print("❌ 虚拟环境未找到，请先创建虚拟环境")
            return
        
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
                generate_report(case_text, charge, statistics_file, merged_file)
                
                step3 = run_command(
                    [str(python_exe), "scripts/generate_word.py",
                     "--input", str(report_file)],
                    "Step 3: 生成Word报告"
                )
                
                if step3:
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