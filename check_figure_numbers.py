#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查论文中图表序号是否正确
"""

import re
from collections import defaultdict

def check_figure_numbers(file_path):
    """检查图表序号"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 提取所有图表
    figures = []
    for line_num, line in enumerate(lines, 1):
        # 匹配【图X-Y ...】格式
        match = re.match(r'^【图(\d+)-(\d+)\s+(.+?)】', line.strip())
        if match:
            chapter = int(match.group(1))
            number = int(match.group(2))
            title = match.group(3)
            figures.append({
                'line': line_num,
                'chapter': chapter,
                'number': number,
                'title': title,
                'full_text': line.strip()
            })
    
    print(f"共找到 {len(figures)} 个图表\n")
    print("=" * 80)
    
    # 按章节分组
    by_chapter = defaultdict(list)
    for fig in figures:
        by_chapter[fig['chapter']].append(fig)
    
    # 检查每个章节
    errors = []
    warnings = []
    
    for chapter in sorted(by_chapter.keys()):
        figs = by_chapter[chapter]
        print(f"\n第{chapter}章：共 {len(figs)} 个图")
        print("-" * 80)
        
        expected_num = 1
        for fig in figs:
            status = "✓" if fig['number'] == expected_num else "✗"
            print(f"{status} 行{fig['line']:4d}: 图{fig['chapter']}-{fig['number']} {fig['title']}")
            
            if fig['number'] != expected_num:
                errors.append({
                    'line': fig['line'],
                    'current': f"{fig['chapter']}-{fig['number']}",
                    'expected': f"{fig['chapter']}-{expected_num}",
                    'title': fig['title']
                })
            
            expected_num = fig['number'] + 1
    
    # 输出错误报告
    print("\n" + "=" * 80)
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个序号错误：\n")
        for err in errors:
            print(f"  行 {err['line']}: 图{err['current']} 应该是 图{err['expected']}")
            print(f"         标题: {err['title']}")
            print()
    else:
        print("\n✅ 所有图表序号正确！")
    
    # 生成修正建议
    if errors:
        print("=" * 80)
        print("\n📝 修正建议：\n")
        
        # 按章节生成正确的序号列表
        for chapter in sorted(by_chapter.keys()):
            figs = by_chapter[chapter]
            print(f"第{chapter}章应该有以下图表：")
            for i, fig in enumerate(figs, 1):
                correct_num = f"{chapter}-{i}"
                current_num = f"{fig['chapter']}-{fig['number']}"
                marker = "  " if current_num == correct_num else "→ "
                print(f"  {marker}图{correct_num} {fig['title']}")
            print()
    
    return errors, figures

if __name__ == '__main__':
    errors, figures = check_figure_numbers('毕业设计论文.txt')
    
    if errors:
        print("\n" + "=" * 80)
        print("需要修正的图表序号：")
        print("=" * 80)
        for err in errors:
            print(f"图{err['current']} → 图{err['expected']}")
