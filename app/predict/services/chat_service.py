import json
import time
from typing import Optional, Generator
import httpx
from sqlalchemy.orm import Session
from app.core.config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL
from app.predict.services.prediction_service import PredictionService
from app.predict.services.portrait_service import PortraitService
from app.predict.services.risk_service import RiskService
from app.predict.services.simulation_service import SimulationService
from app.predict.repositories.chat_session_repository import ChatSessionRepository
from app.predict.services.trace_service import traceable, get_trace_service


SYSTEM_PROMPT = """你是一位专业的初中升学顾问，帮助学生分析考试成绩、预测升学方向、给出提分建议。

重要规则：
1. 必须基于用户提供的上下文数据回答，不要虚构学校名称或概率
2. 引用数据时要具体（如"超过录取线 X 分"、"排名 Y 名"），不要泛泛而谈
3. 给提分建议时必须具体到"每天做什么、练什么题型、达到多少分"，避免"多练习""认真听讲"等空话
4. 回答要分点、结构化，便于学生和家长快速理解
5. 各 prompt 模板中已限定字数，按模板要求执行即可

回答长度（按意图类型区分）：
- 提分咨询：300-400 字（结构化五段式）
- 综合分析：200-300 字
- 志愿选择、风险分析、学习画像：100-200 字

分析维度：
1. 成绩定位 - 当前分数在全区/校的位置
2. 志愿建议 - 冲刺/稳定/保底学校的选择理由
3. 提升方案 - 针对性科目提分建议

输出风格：
- 语气亲切专业，像一位经验丰富的老师
- 给出具体可操作的建议，不是泛泛而谈
- 适当引用数据（如"超过录取线 X 分"）增加说服力
"""

# 意图识别关键词
INTENT_PATTERNS = {
    "提分咨询": ["加", "分", "提分", "涨分", "涨", "提高", "提升", "概率", "能上", "考上", "增加", "变化"],
    "志愿选择": ["选", "哪个", "哪所", "怎么选", "冲", "保底", "稳定", "志愿"],
    "风险分析": ["为什么", "原因", "下滑", "下降", "波动", "不好", "风险"],
    "学习画像": ["学习", "特点", "强项", "弱项", "类型", "风格", "擅长"],
    "综合分析": ["分析", "看看", "怎么样", "情况", "评估", "全面", "总体"],
}

# 学科提分指导模板（按科目给 LLM 提供具体方法，避免空话）
SUBJECT_GUIDANCE = {
    "语文": "重点：阅读理解（每天 1 篇）+ 作文素材积累（每周 2 篇）+ 文言文背诵与字词基础",
    "数学": "重点：基础+中档题保分（每天 10-15 道）+ 压轴题专练（每周 2-3 道）+ 错题本二刷",
    "英语": "重点：单词（每天 20 个）+ 听力（每天 15 分钟）+ 阅读（每天 2 篇）+ 写作模板背诵",
    "物理": "重点：概念公式梳理 + 应用题专练（每天 10 题）+ 实验探究题每周 2 道",
    "化学": "重点：元素周期表与方程式默写 + 选择题保分 + 实验探究题专练",
    "生物": "重点：核心概念记忆 + 图示题训练 + 实验设计题每周 1-2 道",
    "政治": "重点：时事热点 + 主观题答题模板 + 关键词记忆",
    "历史": "重点：时间线与事件因果梳理 + 材料题每周 2 道 + 简答题模板",
    "地理": "重点：地图识读 + 气候/地形知识点 + 综合题训练",
    "道法": "重点：时事热点 + 答题模板 + 关键词记忆",
}

# 首次欢迎语
WELCOME_MESSAGE = """你好！我是升学预测小助手，我可以帮你：

📊 成绩定位 — 看看你的分数能上什么学校
🎯 志愿选择 — 冲刺/稳定/保底怎么选
📈 提分建议 — 加多少分能提升录取概率
⚠️ 风险提示 — 哪些科目需要重点关注
📝 学习画像 — 了解你的学习特点

你想了解哪个？（直接说序号或问题）"""


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = ChatSessionRepository(db)
        self.prediction_service = PredictionService(db)
        self.portrait_service = PortraitService(db)
        self.risk_service = RiskService(db)
        self.simulation_service = SimulationService(db)

    @traceable("ChatService")
    def get_context(self, student_id: int, message_count: int) -> dict:
        """构建上下文"""
        # Get prediction
        from app.predict.repositories.exam_record_repository import ExamRecordRepository
        exam_repo = ExamRecordRepository(self.db)
        latest_records = exam_repo.get_latest_by_student(student_id)
        if not latest_records:
            return {}

        current_score = sum(float(r.score) for r in latest_records) / len(latest_records)
        # Filter to only latest exam's subjects
        if latest_records:
            latest_exam_name = latest_records[0].exam_name
            latest_exam_records = [r for r in latest_records if r.exam_name == latest_exam_name]
            current_score = sum(float(r.score) for r in latest_exam_records)
        prediction = self.prediction_service.predict_student_admission(student_id, current_score)

        # Get portrait
        portrait = self.portrait_service.analyze_student(student_id)

        # Get risk
        risk = self.risk_service.analyze_risk(student_id)

        # Get simulation data for key school
        simulation_results = []
        for increment in [5, 10, 15, 20]:
            new_score = current_score + increment
            new_prediction = self.prediction_service.predict_student_admission(student_id, new_score)
            # Find first non-empty school category
            for category in ["保底", "稳定", "冲刺"]:
                if new_prediction.predictions.get(category):
                    new_school = new_prediction.predictions[category][0]
                    old_school = prediction.predictions.get(category, [None])[0] if prediction.predictions.get(category) else None
                    if old_school:
                        prob_change = new_school.admission_probability - old_school.admission_probability
                    else:
                        prob_change = new_school.admission_probability
                    simulation_results.append({
                        "score_increase": increment,
                        "new_score": new_score,
                        "school_name": new_school.school_name,
                        "probability": new_school.admission_probability,
                        "prob_change": f"+{prob_change}%" if prob_change >= 0 else f"{prob_change}%"
                    })
                    break

        # Build context
        # Get weak subjects analysis
        weak_subjects_data = self._analyze_weak_subjects(student_id)

        context = {
            "current_score": current_score,
            "current_ranking": prediction.current_ranking,
            "predicted_ranking": prediction.predicted_ranking,
            "ranking_trend": prediction.ranking_trend,
            "predictions": prediction.predictions,
            "simulation": simulation_results,
            "portrait": {
                "learning_type": portrait.learning_type if portrait else None,
                "science_ability": portrait.science_ability if portrait else None,
                "english_ability": portrait.english_ability if portrait else None,
                "improvement_potential": portrait.improvement_potential if portrait else None,
            } if portrait else {},
            "risk": {
                "risk_level": risk.risk_level,
                "risk_tags": risk.risk_tags,
            } if risk else {},
            "weak_subjects": weak_subjects_data,
        }
        return context

    def _analyze_weak_subjects(self, student_id: int, limit: int = 100) -> dict:
        """分析薄弱科目：含趋势、最高分参考、提分空间"""
        from collections import defaultdict
        from app.predict.repositories.exam_record_repository import ExamRecordRepository
        exam_repo = ExamRecordRepository(self.db)
        latest_records = exam_repo.get_latest_by_student(student_id, limit=limit)
        if not latest_records or len(latest_records) < 2:
            return {}

        subject_records = defaultdict(list)
        for record in latest_records:
            subject_records[record.subject].append(record)

        subject_analysis = []
        for subject, records in subject_records.items():
            if len(records) < 2:
                continue
            records.sort(key=lambda x: x.exam_time)

            recent_scores = [r.score for r in records[-3:]]
            if len(recent_scores) >= 2:
                if recent_scores[-1] > recent_scores[0]:
                    trend = "上升"
                elif recent_scores[-1] < recent_scores[0]:
                    trend = "下降"
                else:
                    trend = "平稳"
            else:
                trend = "数据不足"

            recent_rankings = [r.ranking for r in records[-3:] if r.ranking is not None]
            ranking_trend = "未知"
            if len(recent_rankings) >= 2:
                if recent_rankings[-1] < recent_rankings[0]:
                    ranking_trend = "排名上升"
                elif recent_rankings[-1] > recent_rankings[0]:
                    ranking_trend = "排名下降"
                else:
                    ranking_trend = "排名平稳"

            max_score = max(r.score for r in records)
            min_score = min(r.score for r in records)
            avg_score = sum(r.score for r in records) / len(records)
            latest_score = records[-1].score
            latest_ranking = records[-1].ranking or 999
            potential_gain = max_score - latest_score

            subject_analysis.append({
                "subject": subject,
                "avg_score": round(avg_score, 1),
                "latest_score": latest_score,
                "latest_ranking": latest_ranking,
                "max_score": max_score,
                "min_score": min_score,
                "trend": trend,
                "ranking_trend": ranking_trend,
                "score_history": recent_scores,
                "potential_gain": potential_gain,
                "exam_count": len(records),
            })

        sorted_subjects = sorted(
            subject_analysis,
            key=lambda x: (x["latest_ranking"], x["potential_gain"]),
            reverse=True,
        )
        return {"weak_subjects": sorted_subjects[:3]}

    @traceable("ChatService")
    def build_prompt(self, context: dict, user_message: Optional[str], message_count: int, session_messages: list = None) -> str:
        """构建LLM提示词"""

        # 首轮无具体问题 → 返回首次欢迎语
        if message_count == 0 and not user_message:
            return WELCOME_MESSAGE

        # 识别用户意图
        intent = self._recognize_intent(user_message or "")

        # 根据意图构建不同的Prompt
        if intent == "提分咨询":
            return self._build_score_increase_prompt(context, user_message)
        elif intent == "志愿选择":
            return self._build志愿_choice_prompt(context, user_message)
        elif intent == "风险分析":
            return self._build_risk_prompt(context, user_message)
        elif intent == "学习画像":
            return self._build_portrait_prompt(context, user_message)
        else:
            # 综合分析或默认
            return self._build_general_prompt(context, user_message, session_messages)

    def _build_score_increase_prompt(self, context: dict, user_message: str) -> str:
        """提分咨询 Prompt（五段式结构化输出）"""
        sim_text = ""
        for sim in context.get("simulation", [])[:4]:
            sim_text += (
                f"  · 加 {sim['score_increase']} 分（总分 {sim['new_score']:.0f}）"
                f" → {sim['school_name']} 概率 {sim['probability']}%"
                f"（变化 {sim['prob_change']}）\n"
            )

        weak_data = context.get("weak_subjects", {})
        weak_subjects = weak_data.get("weak_subjects", [])
        weak_text = ""
        subject_hint_text = ""
        seen_subjects = set()
        if weak_subjects:
            for ws in weak_subjects[:3]:
                history_str = "→".join(str(s) for s in ws.get("score_history", []))
                weak_text += (
                    f"  · {ws['subject']}：最近 {ws['latest_score']} 分"
                    f"（均分 {ws['avg_score']}，历史最高 {ws['max_score']}，最低 {ws['min_score']}），"
                    f"单科排名 {ws['latest_ranking']}，{ws['trend']}（{ws['ranking_trend']}），"
                    f"提分空间约 {ws['potential_gain']} 分（{ws['exam_count']} 次考试）\n"
                    f"    近期成绩：{history_str}\n"
                )
                subj = ws["subject"]
                if subj in SUBJECT_GUIDANCE and subj not in seen_subjects:
                    subject_hint_text += f"  · {subj}：{SUBJECT_GUIDANCE[subj]}\n"
                    seen_subjects.add(subj)

        risk = context.get("risk", {})
        risk_text = (
            f"风险等级：{risk.get('risk_level', '低')}，"
            f"风险点：{', '.join(risk.get('risk_tags', []) or ['无'])}"
        )
        portrait = context.get("portrait", {})
        portrait_text = ""
        if portrait:
            bits = []
            if portrait.get("learning_type"):
                bits.append(f"学习类型：{portrait['learning_type']}")
            if portrait.get("science_ability"):
                bits.append(f"理科：{portrait['science_ability']}")
            if portrait.get("english_ability"):
                bits.append(f"英语：{portrait['english_ability']}")
            if bits:
                portrait_text = "【学习画像】 " + "，".join(bits) + "\n"

        return f"""你是一位经验丰富的初中升学顾问。请基于以下数据，给出**具体可执行**的提分方案。

【学生当前情况】
- 总分：{context.get('current_score', 0):.0f} 分，排名 {context.get('current_ranking', '?')}（{context.get('ranking_trend', '波动')}）
- {risk_text}
{portrait_text}
【薄弱科目分析】（按严重程度排序：ranking 越靠后、提分空间越大越优先）
{weak_text if weak_text else "暂无薄弱科目数据"}

【学科提分参考方法】
{subject_hint_text if subject_hint_text else "暂无"}

【加分模拟】（总分增加后能上的学校）
{sim_text if sim_text else "暂无模拟数据"}

【用户问题】
{user_message}

【输出要求 - 严格按以下五段式】

**1. 现状诊断**
（1-2 句话点出核心问题：哪科最弱、趋势如何、瓶颈是什么）

**2. 提分目标**
（基于"历史最高分"和"提分空间"，给 1-2 个可实现目标，例如"数学 2 周内从 75 提到 85"，并说明可行性）

**3. 具体方法**（最重要！必须具体到动作）
针对每科薄弱点：
- 重点练的题型/模块（如"数学函数与几何证明"、"英语完形填空"）
- 每天/每周练习量（如"每天 10 道选择 + 2 道大题"）
- 资源或方法（如"背诵 20 个高频词组 + 精读 1 篇短文"）

**4. 时间安排**（1-2 周可执行计划）
按天或按周列出：例如"周一三五数学专题，周二四英语阅读"

**5. 预期效果**
结合【加分模拟】数据，告诉用户提分后能进哪一档学校（如"加 10 分有 65% 概率进入 XX 中学"）

【格式与字数】
- 总字数 300-400 字
- 严格分 5 段，每段必答（标题照搬）
- 用具体数字（题数、天数、分数），禁止"多练习""认真听讲"等空话
- 语气亲切专业，像经验丰富的老师在指导学生
"""


    def _build志愿_choice_prompt(self, context: dict, user_message: str) -> str:
        """志愿选择Prompt"""
        predictions_text = ""
        for category in ["冲刺", "稳定", "保底"]:
            schools = context.get("predictions", {}).get(category, [])
            if schools:
                school_names = "、".join([f"{s.school_name}({s.admission_probability}%)" for s in schools[:2]])
                predictions_text += f"{category}：{school_names}；"

        return f"""基于以下【预测数据】，给出选项让用户选择。

【预测结果】
{predictions_text}

用户问题：{user_message}

回答要求：
- 给出A/B/C选项，格式："A. 学校名(概率%)"
- 不要先解释原因
- 50字以内
"""

    def _build_risk_prompt(self, context: dict, user_message: str) -> str:
        """风险分析Prompt"""
        risk_data = context.get("risk", {})
        risk_level = risk_data.get("risk_level", "低")
        risk_tags = risk_data.get("risk_tags", [])

        return f"""基于以下【风险数据】，一句话分析原因。

【风险数据】
风险等级：{risk_level}
风险标签：{', '.join(risk_tags) if risk_tags else '无'}

用户问题：{user_message}

回答要求：
- 一句话简短分析原因
- 50字以内
"""

    def _build_portrait_prompt(self, context: dict, user_message: str) -> str:
        """学习画像Prompt"""
        portrait = context.get("portrait", {})
        learning_type = portrait.get("learning_type", "未知")
        science = portrait.get("science_ability", "未知")
        english = portrait.get("english_ability", "未知")

        return f"""基于以下【画像数据】，描述学生学习特点。

【画像数据】
学习类型：{learning_type}
理科能力：{science}
英语能力：{english}

用户问题：{user_message}

回答要求：
- 描述学习特点
- 50字以内
"""

    def _build_general_prompt(self, context: dict, user_message: str, session_messages: list = None) -> str:
        """综合分析Prompt"""
        predictions_text = ""
        for category in ["冲刺", "稳定", "保底"]:
            schools = context.get("predictions", {}).get(category, [])
            if schools:
                school_names = "、".join([f"{s.school_name}({s.admission_probability}%)" for s in schools[:2]])
                predictions_text += f"{category}：{school_names}；"

        sim_text = ""
        for sim in context.get("simulation", [])[:2]:
            sim_text += f"加{sim['score_increase']}分→{sim['new_score']:.0f}分，概率{sim['probability']}%；"

        history_text = ""
        if session_messages:
            for msg in session_messages[-4:]:
                role = "用户" if msg.get("role") == "user" else "助手"
                history_text += f"\n{role}：{msg.get('content', '')[:200]}"

        return f"""【历史对话】
{history_text}

当前情况：总分{context.get('current_score', 0):.0f}分，排名{context.get('current_ranking', '?')}名（{context.get('ranking_trend', '波动')}）
{predictions_text}
【加分模拟】：{sim_text}
风险：{', '.join(context.get('risk', {}).get('risk_tags', []) or ['无'])}

用户问题：{user_message}

回答要求：
- 结构化输出（分点）
- 100字以内
- 不要先解释原因，直接回答
"""

    def chat(self, student_id: int, message: Optional[str]) -> Generator[dict, None, None]:
        """对话主流程"""
        # 清空上次的trace
        trace = get_trace_service()
        trace.clear()

        # 1. 查活跃会话
        active_session = self.session_repo.get_active_session(student_id, minutes=5)

        if not active_session:
            # 创建新会话
            active_session = self.session_repo.create_session(student_id)
            message_count = 0
        elif active_session.message_count >= 3:
            # 超过3轮，创建新会话
            self.session_repo.delete_old_sessions(student_id, keep_count=1)
            active_session = self.session_repo.create_session(student_id)
            message_count = 0
        else:
            message_count = active_session.message_count

        # 2. 保存用户消息
        if message:
            self.session_repo.append_message(active_session.id, "user", message)

        # 3. 获取上下文
        context = self.get_context(student_id, message_count)
        if not context:
            yield {"content": "抱歉，暂无考试数据，无法进行分析。", "done": True}
            return

        # 4. 获取历史对话（用于追问）
        session_messages = []
        if active_session and message_count > 0:
            session_messages = self.session_repo.get_session_messages(active_session.id)

        # 5. 构建Prompt
        prompt = self.build_prompt(context, message, message_count, session_messages)

        # 5. 调用MiniMax API
        try:
            response_text = self._call_llm(prompt, message_count)
        except Exception as e:
            # 降级：返回规则生成文本
            response_text = self._fallback_response(context)

        # 6. 保存助手回复
        self.session_repo.append_message(active_session.id, "assistant", response_text)
        self.session_repo.increment_count(active_session.id)

               # 7. 流式返回
        for chunk in self._stream_text(response_text):
            yield chunk

        yield {"done": True}

    @traceable("ChatService")
    def _call_llm(self, prompt: str, message_count: int) -> str:
        """调用MiniMax API"""
        if not LLM_API_KEY:
            raise Exception("MiniMax API Key not configured")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        if message_count > 0:
            # 追加历史消息（追问时）
            pass

        messages.append({"role": "user", "content": prompt})

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                }
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            # 去除<think>...</think>思考标签
            import re
            content = re.sub(r'<think>[\s\S]*?</think>', '', content)
            return content

    def _recognize_intent(self, message: str) -> str:
        """识别用户意图

        规则匹配优先，未命中则返回默认的"综合分析"
        """
        if not message or not message.strip():
            return "综合分析"

        message_lower = message.lower()
        for intent, keywords in INTENT_PATTERNS.items():
            for keyword in keywords:
                if keyword in message_lower or keyword in message:
                    return intent
        return "综合分析"

    def _stream_text(self, text: str) -> Generator[dict, None, None]:
        """将文本切分成小块流式返回"""
        for i in range(0, len(text), 10):
            yield {"content": text[i:i+10], "done": False}
            time.sleep(0.02)

    def _fallback_response(self, context: dict) -> str:
        """降级响应：当API不可用时返回规则生成文本"""
        score = context.get("current_score", 0)
        trend = context.get("ranking_trend", "波动")
        portrait = context.get("portrait", {})
        risk = context.get("risk", {})

        response = f"根据你的情况分析：\n\n"
        response += f"1. 成绩定位：你的总分 {score:.0f} 分，排名趋势 {trend}。\n"

        predictions = context.get("predictions", {})
        stretch = predictions.get("冲刺", [])
        stable = predictions.get("稳定", [])
        secure = predictions.get("保底", [])

        if stretch:
            response += f"2. 志愿建议：冲刺学校有 {stretch[0].school_name}（概率 {stretch[0].admission_probability}%）。\n"
        if stable:
            response += f"   稳定学校有 {stable[0].school_name}（概率 {stable[0].admission_probability}%）。\n"
        if secure:
            response += f"   保底学校有 {secure[0].school_name}（概率 {secure[0].admission_probability}%）。\n"

        response += "3. 提分建议：\n"
        weak = context.get("weak_subjects", {}).get("weak_subjects", [])
        if weak:
            for ws in weak[:2]:
                target = max(ws["max_score"], ws["latest_score"] + 5)
                hint = SUBJECT_GUIDANCE.get(ws["subject"], "建议针对性练习并建立错题本")
                response += (
                    f"   · {ws['subject']}（最近 {ws['latest_score']} 分"
                    f"，历史最高 {ws['max_score']}，趋势 {ws['trend']}）："
                    f"目标 2 周内提至 {target} 分。"
                    f"{hint}。\n"
                )
        elif portrait.get("english_ability") == "弱":
            response += "   · 英语是你的弱项，建议每天 20 词 + 1 篇阅读。\n"
        elif portrait.get("science_ability") == "强":
            response += "   · 理科是你的强项，可挑战压轴题进一步拉开差距。\n"
        else:
            response += "   · 建议查漏补缺，每天固定练习薄弱模块。\n"

        sim = context.get("simulation", [])
        if sim:
            s = sim[0]
            response += f"4. 预期：加 {s['score_increase']} 分后 {s['school_name']} 概率 {s['probability']}% ({s['prob_change']})。\n"

        if risk.get("risk_level") == "高":
            tag = risk.get("risk_tags", [None])[0] or "需关注科目"
            response += f"5. 风险提示：{tag}，需要重点关注。"

        return response