"""规则配置热加载——单例模式，启动时加载 tier_rules.json 到内存。"""

import json
from pathlib import Path


class TierConfig:
    _instance = None

    def __init__(self):
        self._path = Path(__file__).parent / "tier_rules.json"
        self._data = self._load()

    def _load(self) -> dict:
        with open(self._path, encoding="utf-8") as f:
            return json.load(f)

    def reload(self) -> None:
        self._data = self._load()

    @property
    def tier_a_percent(self) -> float:
        return self._data["tier_rules"]["A"]["rank_percent"]

    @property
    def tier_b_percent(self) -> float:
        return self._data["tier_rules"]["B"]["rank_percent"]

    @property
    def tier_c_percent(self) -> float:
        return self._data["tier_rules"]["C"]["rank_percent"]

    @property
    def weak_point_threshold(self) -> float:
        return self._data["weak_point"]["threshold"]

    @property
    def low_discrimination_threshold(self) -> float:
        return self._data["question_quality"]["low_discrimination_threshold"]

    @property
    def default_score_line(self) -> int:
        return self._data["enrollment"]["default_score_line"]

    @property
    def borderline_range(self) -> int:
        return self._data["enrollment"]["borderline_range"]

    @property
    def decline_threshold(self) -> float:
        return self._data["trend"]["decline_threshold"]

    @property
    def improve_threshold(self) -> float:
        return self._data["trend"]["improve_threshold"]

    def get_tier_label(self, tier_key: str) -> str:
        return self._data["tier_rules"][tier_key]["label"]

    def get_all_tiers(self) -> dict:
        return self._data["tier_rules"]

    def get_protection_rules(self) -> dict:
        return self._data["protection_rules"]


tier_config = TierConfig()
