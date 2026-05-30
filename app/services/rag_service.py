import json
from app.core.pageindex import PageIndexClient

class RAGService:
    """RAG 检索服务，封装 PageIndex"""

    def __init__(self, workspace: str = None):
        self.client = PageIndexClient(workspace=workspace)
        self.documents = self.client.list_documents()

    def get_all_documents(self) -> str:
        """返回所有文档列表（工具调用用）"""
        docs = [
            {
                'doc_id': doc_id,
                'doc_name': doc.get('doc_name', ''),
                'type': doc.get('type', ''),
                'description': f"包含 {doc.get('line_count', 0)} 行"
            }
            for doc_id, doc in self.documents.items()
        ]
        return json.dumps(docs, ensure_ascii=False)

    def get_document_structure(self, doc_id: str) -> str:
        """返回文档树结构"""
        return self.client.get_document_structure(doc_id)

    def get_page_content(self, doc_id: str, pages: str) -> str:
        """返回指定行号范围的内容"""
        return self.client.get_page_content(doc_id, pages)

    def find_doc_id_by_name(self, name: str) -> str | None:
        """根据书名模糊匹配 doc_id"""
        for doc_id, doc in self.documents.items():
            if name in doc.get('doc_name', ''):
                return doc_id
        return None