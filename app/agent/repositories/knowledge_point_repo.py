"""知识点数据访问层——树形结构查询 + 依赖 DAG 遍历。"""

from sqlalchemy.orm import Session
from app.agent.models.knowledge_point import KnowledgePoint
from app.agent.models.knowledge_dependency import KnowledgeDependency


class KnowledgePointRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_by_subject(self, subject_id: int) -> list[dict]:
        """获取某学科下全部知识点（树形结构）。"""
        rows = (
            self.db.query(KnowledgePoint)
            .filter(KnowledgePoint.subject_id == subject_id)
            .order_by(KnowledgePoint.sort_order.asc())
            .all()
        )
        return [
            {"id": r.id, "name": r.name, "level": r.level,
             "parent_id": r.parent_id, "core_weight": r.core_weight,
             "sort_order": r.sort_order}
            for r in rows
        ]

    def get_tree(self, subject_id: int) -> list[dict]:
        """获取知识点树（嵌套结构）。

        返回章 → 节 → 知识点 的三级嵌套列表。
        """
        all_kps = self.get_by_subject(subject_id)
        chapters = [kp for kp in all_kps if kp["level"] == 1]

        for ch in chapters:
            sections = [kp for kp in all_kps if kp["parent_id"] == ch["id"]]
            ch["children"] = sections
            for sec in sections:
                points = [kp for kp in all_kps if kp["parent_id"] == sec["id"]]
                sec["children"] = points

        return chapters

    def get_children(self, kp_id: int) -> list[dict]:
        """获取某个知识点的直接子节点。"""
        rows = (
            self.db.query(KnowledgePoint)
            .filter(KnowledgePoint.parent_id == kp_id)
            .order_by(KnowledgePoint.sort_order.asc())
            .all()
        )
        return [{"id": r.id, "name": r.name, "level": r.level} for r in rows]

    def get_ancestors(self, kp_id: int) -> list[dict]:
        """获取某个知识点的所有祖先节点（从根到父）。"""
        ancestors = []
        current = self.db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
        while current and current.parent_id:
            parent = (
                self.db.query(KnowledgePoint)
                .filter(KnowledgePoint.id == current.parent_id)
                .first()
            )
            if parent:
                ancestors.append({"id": parent.id, "name": parent.name, "level": parent.level})
                current = parent
            else:
                break
        return list(reversed(ancestors))

    def get_dependencies(self, kp_id: int) -> list[dict]:
        """获取某个知识点的前置依赖关系链。

        从当前知识点出发，沿依赖边向上追溯 (source → target)，
        返回从根依赖到当前知识点的链式路径。
        """
        result = []

        # 当前知识点作为 target 的依赖（source 是前置知识）
        deps = (
            self.db.query(KnowledgeDependency)
            .filter(KnowledgeDependency.target_kp_id == kp_id)
            .all()
        )

        for dep in deps:
            source = (
                self.db.query(KnowledgePoint)
                .filter(KnowledgePoint.id == dep.source_kp_id)
                .first()
            )
            target = (
                self.db.query(KnowledgePoint)
                .filter(KnowledgePoint.id == dep.target_kp_id)
                .first()
            )
            if source and target:
                result.append({
                    "source_id": source.id,
                    "source_name": source.name,
                    "target_id": target.id,
                    "target_name": target.name,
                    "dependency_weight": dep.dependency_weight,
                })

        return result

    def get_dependency_chain(self, kp_id: int) -> list[dict]:
        """获取完整依赖链——从根到当前知识点。

        BFS 遍历依赖图，返回按拓扑序排列的依赖链。
        """
        visited = set()
        chain = []

        def traverse(current_id: int) -> None:
            if current_id in visited:
                return
            visited.add(current_id)

            deps = self.get_dependencies(current_id)
            for dep in deps:
                traverse(dep["source_id"])

            kp = self.db.query(KnowledgePoint).filter(KnowledgePoint.id == current_id).first()
            if kp:
                chain.append({"id": kp.id, "name": kp.name, "level": kp.level})

        traverse(kp_id)
        return chain

    def get_by_ids(self, kp_ids: list[int]) -> list[dict]:
        """批量获取知识点信息。"""
        rows = (
            self.db.query(KnowledgePoint)
            .filter(KnowledgePoint.id.in_(kp_ids))
            .all()
        )
        return [{"id": r.id, "name": r.name, "level": r.level,
                 "parent_id": r.parent_id, "core_weight": r.core_weight}
                for r in rows]
