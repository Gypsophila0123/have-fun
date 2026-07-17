#!/usr/bin/env python3
"""Verify extraction results."""

import json

with open('input/local/local_database.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

cases = data['cases']
print('=== 提取结果验证 ===')
print(f'总案例数: {len(cases)}')
print()
print('案号 | 罪名 | sentence提取 | data_volume提取')
print('-' * 100)

for c in cases:
    sn = c['case_number'][:25]
    ch = c['charge'][:15]
    se = (c['sentence'][:30] if c['sentence'] else '无')
    dv = (c['data_volume'][:20] if c['data_volume'] else '无')
    print(f'{sn:25} | {ch:15} | {se:30} | {dv:20}')

print()
sentence_found = sum(1 for c in cases if c['sentence'])
data_volume_found = sum(1 for c in cases if c['data_volume'])
print(f'sentence提取成功: {sentence_found}/{len(cases)}')
print(f'data_volume提取成功: {data_volume_found}/{len(cases)}')