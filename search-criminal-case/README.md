# 计算机犯罪类案检索项目

本项目提供计算机犯罪案件的类案检索与量刑差异分析工作流，覆盖非法侵入计算机信息系统罪、非法获取计算机信息系统数据罪、非法控制计算机信息系统罪、破坏计算机信息系统罪四个罪名的检索与分析。

**核心功能**：
- 智能要素秒级提取；罪名要件精准匹配；多维类案深度检索；量刑差异量化分析；一键生成专业报告；案例智能去重入库；双引擎驱动检索；本地在线双模式

项目包含多个核心脚本，支持语义检索、关键词检索和本地案例库三种检索方式，输出包含案件概述、罪名分析、类案统计、典型案例评析等内容的完整类案检索报告。

## 快速开始

### 方式一：交互式终端（推荐）

```bash
# 进入项目目录
cd search-criminal-case

# 激活虚拟环境
.venv\Scripts\activate

# 运行交互式入口
python scripts/main.py
```

### 方式二：命令行参数快速模式

```bash
# 指定罪名和案情
python scripts/main.py --charge "非法控制计算机信息系统罪" --case "张某通过植入后门程序，非法控制他人计算机系统"

# 仅指定罪名（交互式输入案情）
python scripts/main.py --charge "非法获取计算机信息系统数据罪"
```

### 方式三：分步执行

```bash
# 1. 合并去重
python scripts/merge_deduplicate.py --input input/local/local_database.json --output output/merged.json

# 2. 统计分析（按罪名过滤）
python scripts/case_statistics.py --input output/merged.json --output output/statistics.json --charge "非法控制计算机信息系统罪"

# 3. 生成Word报告
python scripts/generate_word.py --input output/report.md
```

## 项目结构

```
search-criminal-case/
├── input/                    # 案例数据输入目录
│   ├── semantic/             # 语义检索结果
│   ├── keyword/              # 关键词检索结果
│   ├── local/                # 本地案例库
│   │   └── local_database.json  # 本地案例库主文件（累积式存储）
│   ├── training_data/        # 要素提取反馈训练数据
│   └── case_template.json    # 案例数据录入模板
├── output/                   # 报告输出目录
│   ├── temp/                 # 临时文件目录（自动清理）
│   └── *.docx                # 生成的Word报告
├── config/                   # 配置文件
│   └── default.json          # 默认配置
├── format/                   # 格式规范
│   └── output-format-spec.md # Word输出格式规范
├── references/               # 参考资料
│   ├── crime-elements.md     # 罪名要件参考
│   ├── law-provisions.md     # 法律条文参考
│   └── sentencing-standards.md  # 量刑标准参考
├── scripts/                  # 核心脚本
│   ├── main.py               # 交互式终端入口（要素提取+罪名识别+检索+报告生成）
│   ├── merge_deduplicate.py  # 合并去重脚本
│   ├── case_statistics.py    # 统计分析脚本（支持按罪名过滤）
│   ├── generate_word.py      # Word文档生成器（规范命名：检索报告-日期-时分）
│   ├── save_to_local.py      # 案例入库脚本（累积式存储+自动去重）
│   ├── txt_to_json.py        # TXT文档解析入库
│   ├── rename_cases.py       # 案例文件标准化重命名（案号+罪名）
│   ├── verify_extraction.py  # 字段提取验证工具
│   └── view_cases.py         # 案例浏览工具
└── templates/                # 报告模板
    ├── report-outline.md     # 报告大纲模板
    ├── search-strategy-template.json  # 检索策略模板
    └── case-elements-schema.json      # 要素提取Schema
```

## 数据收录规范

### 数据源优先级

| 优先级 | 数据源 | 说明 |
|--------|--------|------|
| 1 | 最高人民法院指导性案例 | 具有法律效力，优先收录 |
| 2 | 最高人民法院典型案例 | 具有参考价值 |
| 3 | 各高级法院发布的典型案例 | 地域参考 |
| 4 | 中国裁判文书网判决书 | 普通案例补充 |

### 案例筛选标准

- **文书类型**：只收录刑事判决书、刑事裁定书，排除调解书等非实体裁判文书
- **罪名范围**：仅收录以下四个罪名的案例
  1. 非法侵入计算机信息系统罪（《刑法》第285条第1款）
  2. 非法获取计算机信息系统数据罪（《刑法》第285条第2款）
  3. 非法控制计算机信息系统罪（《刑法》第285条第2款）
  4. 破坏计算机信息系统罪（《刑法》第286条）
- **量刑覆盖**：确保每个罪名覆盖不同量刑档次（≤1年、1-3年、3-5年、5年以上）

### JSON字段定义

| 字段名 | 必填 | 说明 | 示例值 |
|--------|------|------|--------|
| case_number | 是 | 案号 | (2023)京0108刑初1234号 |
| title | 是 | 案件标题 | 张三非法获取计算机信息系统数据罪 |
| document_type | 是 | 文书类型 | 刑事判决书 |
| sentence | 是 | 量刑结果（中文数字） | 有期徒刑一年六个月 |
| behavior_type | 是 | 行为类型 | 获取数据 |
| target_system_type | 否 | 目标系统类型 | 普通公司 |
| data_type | 否 | 数据类型 | 个人信息 |
| data_volume | 否 | 数据规模 | 100条 |
| economic_loss | 否 | 经济损失 | 2万元 |
| priority | 否 | 优先级 | guiding/typical/normal |
| court_level | 否 | 法院级别 | 基层人民法院 |

### 文件命名规则

**Word报告命名**：
```
检索报告-[YYYY-MM-DD]-[HHMM].docx          （首次）
检索报告-[YYYY-MM-DD]-[序号]-[HHMM].docx  （同一天多次）
```

示例：
- `检索报告-2026-07-14-1530.docx`
- `检索报告-2026-07-14-2-1600.docx`

**保留机制**：同一天多次检索自动递增序号 + 时分戳，保留所有历史报告，避免覆盖

**案例文件命名**（txt文档）：
```
{案号}_{核心罪名}.txt
```

示例：
- `(2019)川01刑终886号_非法控制计算机信息系统罪.txt`
- `检例第36号_非法获取计算机信息系统数据罪.txt`

**多罪名案件拆分**：当案件涉及多个罪名时，按罪名拆分为多个文件：
```
{案号}_{罪名1}_1.txt
{案号}_{罪名2}_2.txt
```

示例：
- `(2019)川01刑终886号_非法控制_1.txt`
- `(2019)川01刑终886号_破坏_2.txt`

## 检索模式选择

在进行类案检索前，系统会询问用户是否调用北大法宝 MCP：

| 模式 | 触发条件 | 数据源 | 特点 |
|------|----------|--------|------|
| **在线+本地合并模式** | 用户确认调用北大法宝 MCP | MCP语义检索结果（3条/罪名） + 本地案例库 | 数据量充足，结果全面，需消耗token |
| **纯本地模式** | 用户选择不调用或 MCP 不可用 | 仅本地案例库 | 数据量取决于已入库案例，无需消耗token |

**Token节约策略**：
- 每个罪名仅获取3条最相似案例，控制token消耗
- 检索前用户需确认是否调用MCP，避免误消耗
- 案例入库后，下次检索可直接使用本地库，无需重复调用MCP

**重要提示**：在纯本地模式下，如果本地案例库为空或案例数量较少（建议每个罪名至少5条），统计分析结果可能不具备参考价值。请先通过合法渠道收集真实案例并入库。

## 使用流程

### 完整工作流

```bash
# 1. 将案例数据放入 input/semantic/ 或 input/keyword/（MCP检索结果）
# 2. 合并去重（包含本地案例库）
python scripts/merge_deduplicate.py --input input/semantic/*.json input/keyword/*.json input/local/local_database.json --output output/merged.json

# 3. 统计分析
python scripts/case_statistics.py --input output/merged.json --output output/statistics.json

# 4. 生成报告（需先编写 markdown 报告）
python scripts/generate_word.py --input report.md --output output/report.docx --config config/default.json

# 5. 将检索结果入库（可选）
# 方式A：保存指定案号的案例
python scripts/save_to_local.py --input output/merged.json --case-numbers '(2023)京0108刑初1234号' '(2023)沪01刑初5678号' --local-db input/local/local_database.json

# 方式B：保存所有案例
python scripts/save_to_local.py --input output/merged.json --all --local-db input/local/local_database.json
```

### 案例入库说明

`save_to_local.py` 脚本用于将 MCP 检索结果中用户选择的案例保存到本地案例库：

- **累积式存储**：案例追加到 `input/local/local_database.json`，不会覆盖原有数据
- **自动去重**：按案号去重，避免重复入库
- **元数据记录**：记录入库时间、来源等信息

**两种入库方式**：

| 方式 | 命令 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|----------|
| **仅 JSON 入库** | `--all` | 占用空间小、检索速度快 | 只存储结构化数据，无完整判决书 | 快速入库、空间有限 |
| **JSON + txt 文件入库** | `--all --save-txt` | 保留完整判决书内容 | 占用空间大 | 需要完整文书存档 |

示例：
```bash
# 仅 JSON 入库（推荐）
python scripts/save_to_local.py --input output/merged.json --all --local-db input/local/local_database.json

# JSON + txt 文件入库
python scripts/save_to_local.py --input output/merged.json --all --save-txt --local-db input/local/local_database.json
```

下次检索时，`merge_deduplicate.py` 会自动读取本地案例库参与合并分析。

## 配置说明

修改 `config/default.json` 配置文件：

```json
{
  "pkulaw_enabled": true,
  "local_case_library_path": "",
  "report_output_dir": "",
  "max_cases_per_group": 20,
  "parallel_writing": true,
  "default_report_format": "docx",
  "date_range_start": "2018-01-01",
  "date_range_end": "2025-12-31",
  "max_search_results": 50,
  "typical_case_count": 5,
  "word_format": {
    "title_font": "黑体",
    "title_size": 16,
    "heading_font": "黑体",
    "heading_size": 14,
    "body_font": "宋体",
    "body_size": 12,
    "table_font": "宋体",
    "table_size": 10.5,
    "line_spacing": 1.5,
    "margin_top": 2.54,
    "margin_bottom": 2.54,
    "margin_left": 3.17,
    "margin_right": 3.17
  }
}
```

**配置项说明**：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `pkulaw_enabled` | 是否启用北大法宝MCP | true |
| `local_case_library_path` | 本地案例库路径 | 空（自动检测） |
| `report_output_dir` | 报告输出目录 | 空（自动检测） |
| `max_cases_per_group` | 每组最大案例数 | 20 |
| `parallel_writing` | 是否启用并行写作 | true |
| `default_report_format` | 默认报告格式 | docx |
| `date_range_start` | 检索日期范围起始 | 2018-01-01 |
| `date_range_end` | 检索日期范围结束 | 2025-12-31 |
| `max_search_results` | 最大检索结果数 | 50 |
| `typical_case_count` | 典型案例数量 | 5 |