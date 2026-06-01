#!/usr/bin/env python3
"""
四大名著 PageIndex LLM 树结构生成脚本

用法:
    python scripts/rebuild_novels_index.py                    # 默认处理前30章
    python scripts/rebuild_novels_index.py --novel 西游记 --chapters 1-30
    python scripts/rebuild_novels_index.py --novel 西游记 --chapters 31-80 --continue 31
"""

import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.llm_client import call_llm_with_retry
from scripts.llm_prompts import SCENE_ANALYSIS_PROMPT, DIALOGUE_EXTRACTION_PROMPT, CHAPTER_SUMMARY_PROMPT


def parse_chapters_arg(chapters_str: str) -> tuple[int, int]:
    """解析章节范围字符串，如 '1-30' -> (1, 30)"""
    try:
        start, end = chapters_str.split('-')
        return int(start.strip()), int(end.strip())
    except (ValueError, AttributeError) as e:
        raise ValueError(f"无效的章节范围格式: '{chapters_str}', 期望格式如 '1-30'") from e


def load_novel_index(novel_name: str, workspace_dir: Path) -> dict:
    """加载指定小说的索引文件"""
    index_file = workspace_dir / f"{novel_name}_index.json"
    if not index_file.exists():
        raise FileNotFoundError(f"索引文件不存在: {index_file}")
    with open(index_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if "structure" not in data:
        raise ValueError(f"索引文件缺少 'structure' 键: {index_file}")
    return data


def save_novel_index(novel_name: str, workspace_dir: Path, data: dict):
    """保存小说索引文件"""
    index_file = workspace_dir / f"{novel_name}_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def should_process_chapter(chapter: dict, chapter_num: int, args, chapter_start: int, chapter_end: int) -> bool:
    """判断是否需要处理该章节

    自动跳过逻辑:
    - 如果章节已有场景节点（nodes 非空），说明已生成，跳过
    - continue_at 参数可手动指定从哪章继续
    - 检查章节范围
    """
    # 自动检测：已有场景节点则跳过
    if chapter.get('nodes') and len(chapter.get('nodes', [])) > 0:
        return False

    # 增量模式：跳过已存在的章节
    if args.continue_at and chapter_num < args.continue_at:
        return False

    # 检查章节范围
    if chapter_num < chapter_start or chapter_num > chapter_end:
        return False

    return True


def merge_processed_chapters(existing_data: dict, processed_chapters: dict[int, dict], chapter_start: int, chapter_end: int) -> dict:
    """
    合并已存在的索引和新处理的章节

    Args:
        existing_data: 已存在的索引数据
        processed_chapters: 新处理的章节字典，key 为章节编号
        chapter_start: 处理起始章节
        chapter_end: 处理结束章节

    Returns:
        dict: 合并后的索引数据
    """
    existing_structure = existing_data.get("structure", [])

    # 按章节编号替换
    for chapter_num in range(chapter_start, chapter_end + 1):
        idx = chapter_num - 1
        if idx < len(existing_structure):
            # 只更新已处理的章节，跳过已存在且无需更新的
            if chapter_num in processed_chapters:
                existing_structure[idx] = processed_chapters[chapter_num]
        else:
            # 追加新章节（如果超出现有结构）
            if chapter_num in processed_chapters:
                existing_structure.append(processed_chapters[chapter_num])

    existing_data["structure"] = existing_structure
    return existing_data


def extract_scene_text(chapter_text: str, scene_start: int, scene_end: int, chapter_start: int) -> str:
    """根据行号范围提取场景文本"""
    # 边界检查
    if scene_start > scene_end:
        return ''
    lines = chapter_text.split('\n')
    offset_start = max(0, scene_start - chapter_start)
    offset_end = max(0, min(scene_end - chapter_start + 1, len(lines)))
    if offset_start >= len(lines):
        return ''
    return '\n'.join(lines[offset_start:offset_end])


def analyze_scenes(chapter_text: str, chapter_title: str, start_line: int) -> list[dict]:
    """
    调用 LLM 分析章节文本，生成场景列表

    Args:
        chapter_text: 章节原文
        chapter_title: 章节标题
        start_line: 该章节在全文中的起始行号

    Returns:
        list[dict]: 场景列表，每个 dict 包含 title, summary, start_line, end_line
    """
    # 空输入检查
    if not chapter_text or not chapter_text.strip():
        print(f"  警告: 章节 '{chapter_title}' 的文本为空，跳过场景分析")
        return []

    prompt = f"""章节标题: {chapter_title}

请分析以下文本，识别场景切换点。

{SCENE_ANALYSIS_PROMPT}

章节内容:
{chapter_text[:5000]}  # 限制长度避免超出
"""

    result = call_llm_with_retry(prompt)

    if "error" in result:
        print(f"  警告: 场景分析失败 - {result['error']}")
        return []

    scenes = result if isinstance(result, list) else []

    # 验证返回的场景对象
    required_keys = {"title", "summary", "start_line", "end_line"}
    validated_scenes = []
    for scene in scenes:
        if not isinstance(scene, dict):
            print(f"  警告: 跳过无效场景（不是字典）: {scene}")
            continue
        missing_keys = required_keys - set(scene.keys())
        if missing_keys:
            print(f"  警告: 跳过缺少键的场景: 缺少 {missing_keys}, scene: {scene}")
            continue
        validated_scenes.append(scene)
    scenes = validated_scenes

    # 校正行号（加上章节起始行号偏移）
    for scene in scenes:
        if "start_line" in scene:
            scene["start_line"] += start_line - 1
        if "end_line" in scene:
            scene["end_line"] += start_line - 1

    # 验证行号范围
    validated_scenes = []
    for scene in scenes:
        if scene.get("start_line", 0) > scene.get("end_line", 0):
            print(f"  警告: 跳过行号范围无效的场景: start_line > end_line, scene: {scene}")
            continue
        validated_scenes.append(scene)
    scenes = validated_scenes

    return scenes


def extract_dialogues(scene_text: str, scene_title: str, start_line: int) -> list[dict]:
    """
    调用 LLM 从场景文本中提取对话和旁白

    Args:
        scene_text: 场景原文
        scene_title: 场景标题
        start_line: 该场景在章节中的起始行号（注：对话节点不包含行号信息，L3 节点仅包含 speaker 和 text）

    Returns:
        list[dict]: 对话节点列表，每个 dict 包含 speaker, text
    """
    prompt = f"""场景标题: {scene_title}

请分析以下场景文本，提取每一句对话和旁白。

{DIALOGUE_EXTRACTION_PROMPT}

场景内容:
{scene_text[:3000]}  # 限制长度
"""

    result = call_llm_with_retry(prompt)

    if "error" in result:
        print(f"  警告: 对话提取失败 - {result['error']}")
        return []

    dialogues = result if isinstance(result, list) else []

    # 验证对话对象
    required_keys = {"speaker", "text"}
    validated_dialogues = []
    for dialogue in dialogues:
        if not isinstance(dialogue, dict):
            print(f"  警告: 跳过无效对话（不是字典）: {dialogue}")
            continue
        missing_keys = required_keys - set(dialogue.keys())
        if missing_keys:
            print(f"  警告: 跳过缺少键的对话: 缺少 {missing_keys}, dialogue: {dialogue}")
            continue
        validated_dialogues.append(dialogue)
    return validated_dialogues


def process_chapter(chapter: dict, chapter_num: int) -> dict:
    """
    处理单个章节，生成带场景和对话的树结构

    Args:
        chapter: 原始章节数据（包含 text 和 title）
        chapter_num: 章节编号

    Returns:
        dict: 处理后的章节节点，包含：
            - node_id: 格式为 f"{chapter_num:04d}" (如 "0001")
            - title: 章节标题
            - summary: 章节摘要
            - start_line: 起始行号
            - end_line: 结束行号
            - nodes: 子节点列表（场景节点列表）
    """
    # 验证 chapter_num
    if chapter_num <= 0:
        print(f"  警告: 章节编号 {chapter_num} 无效（必须 > 0），跳过")
        return {
            "node_id": f"ERR_{chapter_num:04d}",
            "title": chapter.get('title', '无标题'),
            "summary": '',
            "start_line": chapter.get('start_line', 0),
            "end_line": chapter.get('end_line', 0),
            "nodes": []
        }

    chapter_title = chapter.get('title', '无标题')
    chapter_text = chapter.get('text', '')
    chapter_start_line = chapter.get('start_line', 0)
    chapter_end_line = chapter.get('end_line', 0)

    # 验证行号范围
    if chapter_start_line > chapter_end_line:
        print(f"  警告: 章节 '{chapter_title}' 的行号范围无效（start_line={chapter_start_line} > end_line={chapter_end_line}），跳过")
        return {
            "node_id": f"{chapter_num:04d}",
            "title": chapter_title,
            "summary": '',
            "start_line": chapter_start_line,
            "end_line": chapter_end_line,
            "nodes": []
        }

    # 空文本检查
    if not chapter_text.strip():
        print(f"  警告: 章节 '{chapter_title}' 的文本为空，返回空节点")
        return {
            "node_id": f"{chapter_num:04d}",
            "title": chapter_title,
            "summary": '',
            "start_line": chapter_start_line,
            "end_line": chapter_end_line,
            "nodes": []
        }

    # 1. 生成章节摘要
    summary_prompt = f"""章节标题: {chapter_title}

请为以下章节生成简短摘要（100字以内）。

{CHAPTER_SUMMARY_PROMPT}

章节内容:
{chapter_text[:5000]}
"""
    result = call_llm_with_retry(summary_prompt)
    if "error" in result:
        print(f"  警告: 章节摘要生成失败 - {result['error']}")
        chapter_summary = ''
    else:
        chapter_summary = result.get('summary', '') if isinstance(result, dict) else ''

    # 2. 分析场景
    scenes = analyze_scenes(chapter_text, chapter_title, chapter_start_line)

    # 3. 处理每个场景
    scene_nodes = []
    for scene in scenes:
        scene_title = scene.get('title', '无标题场景')
        scene_start = scene.get('start_line', 0)
        scene_end = scene.get('end_line', 0)
        scene_summary = scene.get('summary', '')

        # 提取场景文本
        scene_text = extract_scene_text(chapter_text, scene_start, scene_end, chapter_start_line)

        # 提取对话
        dialogue_nodes = extract_dialogues(scene_text, scene_title, scene_start)

        # 构建场景节点（L2）
        scene_nodes.append({
            "title": scene_title,
            "summary": scene_summary,
            "start_line": scene_start,
            "end_line": scene_end,
            "nodes": dialogue_nodes  # L3 节点列表
        })

    # 4. 构建章节节点（L1）
    return {
        "node_id": f"{chapter_num:04d}",
        "title": chapter_title,
        "summary": chapter_summary,
        "start_line": chapter_start_line,
        "end_line": chapter_end_line,
        "nodes": scene_nodes
    }


def main():
    parser = argparse.ArgumentParser(description="LLM 驱动的 PageIndex 树结构重建")
    parser.add_argument("--novel", type=str, help="小说名称（如：西游记）")
    parser.add_argument("--chapters", type=str, default="1-30", help="章节范围，如 1-30")
    parser.add_argument("--continue-at", type=int, default=None, help="从指定章节继续生成（增量追加模式）")
    parser.add_argument("--model", type=str, default=None, help="LLM 模型名称")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    workspace_dir = project_root / "workspace" / "novels"

    # 确定要处理的小说列表
    if args.novel:
        novels = [args.novel]
    else:
        novels = [f.stem.replace('_index', '') for f in workspace_dir.glob("*_index.json")]

    # 解析章节范围
    chapter_start, chapter_end = parse_chapters_arg(args.chapters)

    for novel in novels:
        print(f"\n{'='*60}")
        print(f"处理小说: {novel}")
        print(f"章节范围: {chapter_start}-{chapter_end}")
        if args.continue_at:
            print(f"增量模式: 从第 {args.continue_at} 章继续")
        print(f"{'='*60}")

        index_data = load_novel_index(novel, workspace_dir)

        # 处理指定章节
        processed_chapters = {}
        for i, chapter in enumerate(index_data["structure"]):
            chapter_num = i + 1

            # 判断是否需要处理该章节（自动跳过已生成的）
            if not should_process_chapter(chapter, chapter_num, args, chapter_start, chapter_end):
                print(f"  [跳过] 第{chapter_num}章已存在场景节点")
                continue

            try:
                print(f"\n--- 第{chapter_num}章: {chapter.get('title', 'N/A')} ---")
                processed = process_chapter(chapter, chapter_num)
                processed_chapters[chapter_num] = processed
            except Exception as e:
                print(f"  [警告] 处理第{chapter_num}章时出错: {e}")
                continue  # 继续处理下一章，避免整个脚本崩溃

        # 合并处理结果
        if processed_chapters:
            index_data = merge_processed_chapters(index_data, processed_chapters, chapter_start, chapter_end)
            save_novel_index(novel, workspace_dir, index_data)
            print(f"\n已保存 {len(processed_chapters)} 个章节的索引更新")


if __name__ == "__main__":
    main()