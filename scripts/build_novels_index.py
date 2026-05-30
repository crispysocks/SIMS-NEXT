#!/usr/bin/env python3
"""
四大名著索引构建脚本
运行: python scripts/build_novels_index.py
"""

import os
import re
import json
from pathlib import Path

CHAPTER_PATTERN = re.compile(r'^第([一二三四五六七八九十百千万零\d]+)回\s+(.+)$')
RESOURCES_DIR = Path(__file__).parent.parent / "resources"
WORKSPACE_DIR = Path(__file__).parent.parent / "workspace" / "novels"

def parse_chapters(text: str) -> list[dict]:
    """解析文本，提取章节列表"""
    lines = text.split('\n')
    chapters = []
    node_counter = 1

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue

        match = CHAPTER_PATTERN.match(stripped)
        if match:
            # 收集该章节内容直到下一个章节
            content_lines = []
            for next_line in lines[line_num:]:
                next_stripped = next_line.strip()
                if not next_stripped:
                    continue
                if CHAPTER_PATTERN.match(next_stripped):
                    break
                # 清洗 HTML 标签
                clean = re.sub(r'<[^>]+>', '', next_line)
                if clean.strip():
                    content_lines.append(clean)

            chapters.append({
                'node_id': f"{node_counter:04d}",
                'title': f"第{match.group(1)}回 {match.group(2)}",
                'line_num': line_num,
                'text': '\n'.join(content_lines[:100]),  # 限制长度
                'nodes': []
            })
            node_counter += 1

    return chapters

def main():
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    for txt_file in RESOURCES_DIR.glob("*.txt"):
        print(f"Processing {txt_file.name}...")

        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        doc_name = txt_file.stem.replace('《', '').replace('》', '')
        chapters = parse_chapters(content)
        print(f"  Found {len(chapters)} chapters")

        index_data = {
            'doc_name': doc_name,
            'line_count': content.count('\n') + 1,
            'structure': chapters
        }

        output_file = WORKSPACE_DIR / f"{doc_name}_index.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"  Saved to {output_file}")

    # 生成 _meta.json
    meta = {}
    for idx_file in WORKSPACE_DIR.glob("*_index.json"):
        with open(idx_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        doc_id = idx_file.stem.replace('_index', '')
        meta[doc_id] = {
            'doc_name': data['doc_name'],
            'type': 'novel',
            'path': str(idx_file),
            'line_count': data['line_count']
        }

    with open(WORKSPACE_DIR / "_meta.json", 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(meta)} novels indexed.")
    print(f"Index files: {WORKSPACE_DIR}")

if __name__ == "__main__":
    main()