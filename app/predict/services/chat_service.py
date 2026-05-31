import json
import time
from typing import Optional, Generator
import httpx
from sqlalchemy.orm import Session
from app.core.config import MINIMAX_API_KEY, MINIMAX_MODEL
from app.predict.services.prediction_service import PredictionService
from app.predict.services.portrait_service import PortraitService
from app.predict.services.risk_service import RiskService
from app.predict.services.simulation_service import SimulationService
from app.predict.repositories.chat_session_repository import ChatSessionRepository
from app.predict.services.trace_service import traceable, get_trace_service


SYSTEM_PROMPT = """你是一位专业的初中升学顾问，帮助学生分析考试成绩、预测升学方向、给出提分建议。

重要规则：
1. 必须基于用户提供的上下文数据进行回答，不要虚构学校名称或概率
2. 如果上下文中有"保底学校"、"稳定学校"、"冲刺学校"信息，必须从数据中提取回答
3. 如果上下文中有"加分模拟"数据，回答加分相关问题时必须引用该数据
4. 回答要简洁具体，控制在200字以内

分析维度：
1. 成绩定位 - 当前分数在全区/校的位置
2. 志愿建议 - 冲刺/稳定/保底学校的选择理由
3. 提升方案 - 针对性科目提分建议

输出风格：
- 语气亲切专业，像一位经验丰富的老师
- 给出具体可操作的建议，不是泛泛而谈
- 适当引用数据（如"超过录取线X分"）增加说服力
- 字数控制在200字以内
"""

# 意图识别关键词
INTENT_PATTERNS = {
    "提分咨询": ["加", "分", "概率", "提升", "能上", "考上", "增加", "变化"],
    "志愿选择": ["选", "哪个", "哪所", "怎么选", "冲", "保底", "稳定", "志愿"],
    "风险分析": ["为什么", "原因", "下滑", "下降", "波动", "不好", "风险"],
    "学习画像": ["学习", "特点", "强项", "弱项", "类型", "风格", "擅长"],
    "综合分析": ["分析", "看看", "怎么样", "情况", "评估", "全面", "总体"],
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

    def _analyze_weak_subjects(self, student_id: int, limit: int = 50) -> dict:
        """分析薄弱科目"""
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
            latest_ranking = records[-1].ranking or 999
            avg_score = sum(r.score for r in records) / len(records)
            subject_analysis.append({
                "subject": subject,
                "avg_score": avg_score,
                "latest_score": records[-1].score,
                "latest_ranking": latest_ranking,
            })

        sorted_subjects = sorted(subject_analysis, key=lambda x: x["latest_ranking"])
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
        """提分咨询Prompt"""
        sim_text = ""
        for sim in context.get("simulation", [])[:4]:
            sim_text += f"加{sim['score_increase']}分→{sim['new_score']:.0f}分，{sim['school_name']}概率{sim['probability']}%，变化{sim['prob_change']}；"

        weak_data = context.get("weak_subjects", {})
        weak_subjects = weak_data.get("weak_subjects", [])
        weak_text = ""
        if weak_subjects:
            for ws in weak_subjects[:3]:
                weak_text += f"{ws['subject']}({ws['latest_score']}分,排名{ws['latest_ranking']})；"

        return f"""基于以下数据，回答用户关于提分的问题。

【加分模拟数据】（总分变化）：
{sim_text if sim_text else "暂无模拟数据"}

【薄弱科目分析】：
{weak_text if weak_text else "暂无科目数据"}

用户问题：{user_message}

回答要求：
- 先指出薄弱科目，给出针对性建议
- 如果有模拟数据，引用具体概率变化
- 50字以内
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
        if not MINIMAX_API_KEY:
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
                "https://api.minimax.chat/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MINIMAX_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MINIMAX_MODEL,
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
        response += f"1. 成绩定位：你的分数{score:.0f}分，排名{trend}。\n"

        predictions = context.get("predictions", {})
        stretch = predictions.get("冲刺", [])
        stable = predictions.get("稳定", [])
        secure = predictions.get("保底", [])

        if stretch:
            response += f"2. 志愿建议：冲刺学校有{stretch[0].school_name}（概率{stretch[0].admission_probability}%）。\n"
        if stable:
            response += f"   稳定学校有{stable[0].school_name}（概率{stable[0].admission_probability}%）。\n"
        if secure:
            response += f"   保底学校有{secure[0].school_name}（概率{secure[0].admission_probability}%）。\n"

        response += f"3. 提分建议："
        if portrait.get("english_ability") == "弱":
            response += "英语是你的弱项，建议加强阅读训练。"
        elif portrait.get("science_ability") == "强":
            response += "理科是你的强项，可以适当挑战难题。"

        if risk.get("risk_level") == "高":
            response += f"\n风险提示：{risk.get('risk_tags', [])[0] if risk.get('risk_tags') else ''}，需要关注。"

        return response