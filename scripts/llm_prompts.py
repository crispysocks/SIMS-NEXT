"""
LLM Prompts for Classical Novel Analysis

This module contains prompt templates used by the PageIndex LLM tree reconstruction
pipeline for scene analysis, dialogue extraction, and chapter summarization.
"""

# Scene Analysis Prompt - Identify scene transitions in classical novel text
SCENE_ANALYSIS_PROMPT = """你是一个古典小说分析专家。请分析以下文本，识别场景切换点。

重要：只输出 JSON 数组，不要有任何其他文字。

场景切换的判断标准：
- 时间发生变化（如：清晨→午后、夜间→次日）
- 地点/场景发生变化（如：府中→街头、山上→水中）
- 人物活动场所发生变化

请为每个场景输出：
- title：场景标题（简洁描述时间+地点，如"花果山石猴诞生"）
- summary：场景内容概括（50字以内）
- start_line：该场景在原文中的起始行号
- end_line：该场景在原文中的结束行号

只输出 JSON 数组，不要有前缀或后缀文字。
"""

# Dialogue Extraction Prompt - Extract dialogues and narration from scene text
DIALOGUE_EXTRACTION_PROMPT = """你是一个古典小说分析专家。请分析以下场景文本，提取其中的对话和旁白。

重要：只输出 JSON 数组，不要有任何其他文字。格式要求：
- 每一句话都属于一个说话人（人物名称或"旁白"）
- 按出现顺序依次标注每句话
- 保留原文文字，不做任何修改
- 旁白也作为独立的说话人

请为每句话输出：
- speaker：说话人名称
- text：说话内容原文

只输出 JSON 数组，不要有前缀或后缀文字。
"""

# Chapter Summary Prompt - Generate brief chapter summary
CHAPTER_SUMMARY_PROMPT = """你是一个古典小说分析专家。请为以下章回生成简要概述。

要求：
- summary：章节内容概括（100字以内）

输出JSON格式：
{"summary": "..."}
"""