"""LLM 输出结构化校验——Pydantic v2 Schema + 空话检测。"""

from pydantic import BaseModel, Field, field_validator


BANNED_PHRASES = [
    "加强练习", "提高兴趣", "关注基础", "多做题目",
    "强化训练", "重视教学", "巩固知识", "注意方法",
]


class SuggestionItem(BaseModel):
    knowledge_point: str = Field(..., min_length=2, description="针对哪个知识点")
    target_students: str = Field(..., min_length=2, description="针对哪类学生")
    question_type: str = Field(..., min_length=2, description="针对哪种题型或能力")
    teaching_action: str = Field(..., min_length=10, description="具体可操作的教学行为")
    expected_goal: str = Field(..., min_length=5, description="可量化的提升目标")

    @field_validator("teaching_action")
    @classmethod
    def reject_banned_phrases(cls, v: str) -> str:
        for phrase in BANNED_PHRASES:
            if phrase in v:
                raise ValueError(f"包含禁止空话: '{phrase}'")
        return v

    @field_validator("teaching_action")
    @classmethod
    def reject_short_action(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("teaching_action 过短，可能为空话")
        return v


class AnalysisReport(BaseModel):
    """综合报告结构（PRD 定义 + 多轮对话场景扩展）。"""

    weak_kp_remediation: list[SuggestionItem] = Field(default_factory=list)
    tier_strategies: dict[str, list[SuggestionItem]] = Field(default_factory=dict)
    borderline_intervention: list[SuggestionItem] = Field(default_factory=list)
    overall_direction: str = Field(default="", max_length=500)


def validate_llm_output(data: dict) -> AnalysisReport | None:
    """校验 LLM 输出的 JSON，返回 None 表示校验失败。"""
    try:
        return AnalysisReport.model_validate(data)
    except Exception:
        return None


def validate_suggestion_items(items: list[dict]) -> tuple[list[SuggestionItem], list[str]]:
    """批量校验建议项，返回 (通过项, 错误列表)。"""
    valid = []
    errors = []
    for i, item in enumerate(items):
        try:
            valid.append(SuggestionItem.model_validate(item))
        except Exception as e:
            errors.append(f"第 {i + 1} 条建议校验失败: {e}")
    return valid, errors
