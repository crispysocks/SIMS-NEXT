from sqlalchemy.orm import Session
from app.predict.models.score_rank_line import ScoreRankLine


class ScoreRankLineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_score(self, score: float, region: str, year: int) -> ScoreRankLine | None:
        """根据分数查对应的一分一段表记录"""
        return self.db.query(ScoreRankLine).filter(
            ScoreRankLine.region == region,
            ScoreRankLine.year == year,
            ScoreRankLine.score_min <= score,
            ScoreRankLine.score_max >= score,
            ScoreRankLine.is_deleted == False
        ).first()

    def score_to_rank(self, score: float, region: str, year: int) -> int:
        """将分数转换为排名"""
        line = self.get_by_score(score, region, year)
        if not line:
            return 50000  # 低于最低分段的默认排名

        # 计算在分数段内的排名位置
        segment_position = (score - line.score_min) / (line.score_max - line.score_min + 1)
        rank_in_segment = line.rank_min + int(segment_position * (line.rank_max - line.rank_min))
        return rank_in_segment

    def get_rank_range(self, region: str, year: int) -> tuple[int, int]:
        """获取某地区某年的总考生人数范围"""
        line = self.db.query(ScoreRankLine).filter(
            ScoreRankLine.region == region,
            ScoreRankLine.year == year,
            ScoreRankLine.is_deleted == False
        ).order_by(ScoreRankLine.rank_max.desc()).first()

        if line:
            return (1, line.rank_max)
        return (1, 50000)
