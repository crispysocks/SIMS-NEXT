import json
import os
from pathlib import Path
from app.core.pageindex import PageIndexClient

class RAGService:
    """RAG 检索服务，封装 PageIndex"""

    def __init__(self, workspace: str = None):
        if workspace is None:
            workspace = Path(__file__).parent.parent.parent / "workspace" / "novels"
        self.client = PageIndexClient(workspace=str(workspace))

    def get_all_documents(self) -> str:
        """返回所有文档列表（工具调用用）"""
        docs = self.client.list_documents()
        return json.dumps(docs, ensure_ascii=False)

    def get_document_structure(self, doc_id: str) -> str:
        """返回文档树结构"""
        return self.client.get_document_structure(doc_id)

    def get_page_content(self, doc_id: str, pages: str) -> str:
        """返回指定行号范围的内容"""
        return self.client.get_page_content(doc_id, pages)

    def find_doc_id_by_name(self, name: str) -> str | None:
        """根据书名模糊匹配 doc_id"""
        for doc in self.client.list_documents():
            if name in doc.get('doc_name', ''):
                return doc.get('doc_id')
        return None