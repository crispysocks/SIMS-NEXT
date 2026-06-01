---
name: novel-semantic-parser
description: |
  Structure novel text into Book→Chapter→Scene→Dialogue JSON hierarchy. Load this skill
  when user asks to "分析小说", "结构化章节", "提取对话", "预处理小说",
  "按 schema 提取章回", or provides a novel file and asks for semantic parsing.
  Do NOT load when: user wants to read/chat about novel content (no parsing needed),
  translate novel text, generate novel text, or classify sentiment/genre — those are
  separate skills. Do NOT load for binary files (PDF/docx/epub); ask user to convert
  to plain .txt first.
---

# Novel Semantic Parser

## Overview

Convert raw novel text into a structured Book→Chapter→Scene→Dialogue JSON. The output
serves downstream tasks: character network analysis, dialogue generation, scene
visualization, etc. **Garbage in → garbage out** — imprecise boundaries mean wrong
scene groupings and missed dialogues.

## Iron Law

```
NO COMPLETION CLAIM WITHOUT CONFIRMING OUTPUT FILE EXISTS AND IS VALID JSON
```

Before telling the user "搞定" or "结构化完成", you MUST verify:
1. The output file was actually written to disk
2. The file is valid JSON (parse-able)
3. At least one chapter, scene, and dialogue entry exist

---

## Inputs to collect

- **Novel file path** — confirm the file exists and is readable plain text (.txt)
- **Schema variant** — default is the standard Book→Chapter→Scene→Dialogue hierarchy.
  If user specifies a different schema, note it before starting.
- **Novel type** — classical Chinese or modern. This affects dialogue boundary heuristics.
  If unclear, infer from file encoding and content style, then proceed.

---

## Procedure

### Phase 1: Parse and Verify Input

1. Confirm the file is plain text (`.txt`). If binary (PDF/docx/epub/mobi):
   → Tell the user to convert to `.txt` first. Do NOT attempt format conversion inside
   the skill. Stop here.

2. Read the file in full. Log the total character count.

### Phase 2: Detect Chapter Boundaries

Detect boundaries by scanning these patterns in order of priority:

| Priority | Pattern | Example |
|----------|---------|---------|
| 1 | Regex: `^(第[一二三四五六七八九十百千\\d]+[回章篇]|Chapter\\s*\\d+|第?[0-9]+\\.)` | 第一回、Chapter 3、第3. |
| 2 | Blank line + title line combo | (blank) + 红楼梦 |
| 3 | Horizontal rule | `========` 或 `——` 行 |
| 4 | Fixed-length fallback | If none above: chunk by ~5000 chars |

When falling back to fixed-length chunking, warn the user: "章节边界未检测到，
降级为固定长度分块，精度可能受影响。"

### Phase 3: Segment Scenes Within Each Chapter

- Scene break = location/place change, or a hard divider (`========` / `——`)
- If no clear divider, group paragraphs by narrative coherence
- Each scene gets a `summary` field (≤ 50 chars). If summarizing is unclear, use
  the first line of the scene as the summary instead.

### Phase 4: Extract Dialogues Within Each Scene

| Situation | Speaker | Content |
|-----------|---------|---------|
| Explicit quote or `"XX道："` pattern | Extract speaker name | Full original text incl. action/gesture description |
| Narrative / no clear speaker | `"旁白"` | The entire paragraph |
| Single sentence with implied speaker | `"旁白"` | That sentence |

- Each independent utterance = one entry in `dialogues[]`
- Consecutive lines from the same speaker: merge into one entry with `\n` separator

### Phase 5: Assemble and Write Output

1. Build the JSON structure per the Output contract below.
2. Write to `<input-dir>/<original-filename>-parsed.json`
   原因：放在源文件同目录便于用户查找；`-parsed` 后缀区分原始文件
3. Report summary: total chapters, scenes, dialogues, output file path

---

## Output contract

```json
{
  "title": "<书名，从文件名或文内提取，无则 null>",
  "author": "<文内提取，无则 null>",
  "chapters": [
    {
      "id": 1,
      "title": "<章节标题>",
      "scenes": [
        {
          "id": 1,
          "summary": "<场景摘要，≤50字>",
          "dialogues": [
            {
              "speaker": "<说话人或旁白>",
              "content": "<完整原文，含动作神态>"
            }
          ]
        }
      ]
    }
  ]
}
```

One JSON file next to the input. No intermediate files, no progress files,
no chunk outputs — final output only.

---

## Verification (Evidence Before Claims)

BEFORE saying "完成" / "搞定":

- [ ] Output file exists at the path you named
- [ ] File parses as valid JSON (no trailing commas, no unclosed brackets)
- [ ] At least 1 chapter, 1 scene, 1 dialogue entry present
- [ ] All `speaker` fields are non-empty strings

If any check fails → report the actual failure, do not claim success.

---

## Failure Handling

| Failure | Response |
|---------|----------|
| File not found | Ask user for correct path. Do not guess. |
| Not plain text | Tell user to convert to `.txt`. Do not attempt conversion. |
| No chapter boundaries detected | Fall back to 5000-char fixed chunking. Warn user. |
| Empty dialogues in a scene | Keep the scene; include it but note the scene may be mis-parsed |
| JSON write fails (permission/disk) | Report error with path. Do not retry silently. |
| Output file parse fails | Report the JSON parse error line. Offer to re-run. |

---

## Rationalization Table

These excuses mean: **you skipped a step, fix it**.

| Excuse | Reality |
|--------|---------|
| "File is too big, I'll sample instead of reading full" | Incomplete read → wrong chapter boundaries. Read it all. |
| "I'll parse as I go and skip writing the file" | No artifact = task not done. Write the file. |
| "This chapter has no dialogues, skip it" | Zero dialogues is suspicious — check if speaker pattern was missed |
| "Just assume the schema matches" | Schema mismatch → downstream scripts break. Confirm before writing |
| "I'll skip the verification step" | Iron Law violation. Verify or do not claim completion |
| "Fixed-length is good enough" | Only use as last resort fallback. Warn user first. |
| "I'll merge all scenes into one" | Loses location granularity. Reject unless file is ≤ 2000 chars |

---

## Red Flags — STOP and Correct

- Saying "搞定" / "完成" without confirming the output file exists
- Writing to a path without first reading the input file
- Skipping chapter boundary detection and going straight to dialogue extraction
- Having zero `"旁白"` entries — every scene has narration, if you see none, parsing is broken
- Output JSON has fewer entries than chapters (every chapter needs ≥1 scene)
- Total dialogues = 0 — something went wrong, do not report success
- Output file not valid JSON but you said "结构化完成"

---

## Examples

**Input**: User uploads `D:\novels\hongloumeng.txt` and says "帮我结构化一下"

**Process**:
1. Confirm file is `.txt` → read full text (~80k chars)
2. Detect chapter boundaries → 120 chapters found
3. Segment scenes → ~400 scenes
4. Extract dialogues → ~3000 entries
5. Write to `D:\novels\hongloumeng-parsed.json`

**Output excerpt**:
```json
{
  "title": "红楼梦",
  "author": "曹雪芹",
  "chapters": [
    {
      "id": 1,
      "title": "第一回 甄士隐梦幻识通灵",
      "scenes": [
        {
          "id": 1,
          "summary": "甄士隐与贾雨村相遇，提及通灵宝玉",
          "dialogues": [
            {
              "speaker": "旁白",
              "content": "此开卷第一回也。作者自云：因曾历过一番梦幻之后，故将真事隐去，而借通灵之说，撰此《石头记》也。"
            },
            {
              "speaker": "二仙师",
              "content": "善哉，善哉！待我再细细指点，待他日后蝉蜕之时，度往彼岸。"
            }
          ]
        }
      ]
    }
  ]
}
```

**Input**: "预处理这本小说" without specifying a file
→ Ask user to provide the file path first.