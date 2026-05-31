import os
import uuid
import json
from pathlib import Path

import PyPDF2

from .utils import ConfigLoader, remove_fields

META_INDEX = "_meta.json"


def _normalize_retrieve_model(model: str) -> str:
    """保留支持的 Agents SDK 前缀，其他提供商路径通过 LiteLLM 路由"""
    passthrough_prefixes = ("litellm/", "openai/")
    if not model or "/" not in model:
        return model
    if model.startswith(passthrough_prefixes):
        return model
    return f"litellm/{model}"


class PageIndexClient:
    """
    文档索引和检索客户端
    流程: index() -> get_document() / get_document_structure() / get_page_content()
    """
    def __init__(self, api_key: str = None, model: str = None, retrieve_model: str = None, workspace: str = None):
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        elif not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY", "")
        self.workspace = Path(workspace).expanduser() if workspace else None
        overrides = {}
        if model:
            overrides["model"] = model
        if retrieve_model:
            overrides["retrieve_model"] = retrieve_model
        opt = ConfigLoader().load(overrides or None)
        self.model = opt.model
        self.retrieve_model = _normalize_retrieve_model(opt.retrieve_model or self.model)
        if self.workspace:
            self.workspace.mkdir(parents=True, exist_ok=True)
        self.documents = {}
        if self.workspace:
            self._load_workspace()

    def index(self, file_path: str, mode: str = "auto") -> str:
        """索引文档，返回 document_id"""
        file_path = os.path.abspath(os.path.expanduser(file_path))
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc_id = str(uuid.uuid4())
        ext = os.path.splitext(file_path)[1].lower()

        # 注意: 实际的 PDF/Markdown 索引功能需要 page_index 和 page_index_md 模块
        # 此处仅为框架实现，完整功能需参考 reference/PageIndex/pageindex/
        is_pdf = ext == '.pdf'
        is_md = ext in ['.md', '.markdown']

        if mode == "pdf" or (mode == "auto" and is_pdf):
            print(f"Indexing PDF: {file_path}")
            # 从预建 JSON 文件加载索引的简单占位实现
            self.documents[doc_id] = {
                'id': doc_id,
                'type': 'pdf',
                'path': file_path,
                'doc_name': os.path.basename(file_path),
                'doc_description': '',
                'page_count': len(PyPDF2.PdfReader(file_path).pages),
                'structure': [],
                'pages': [],
            }
        elif mode == "md" or (mode == "auto" and is_md):
            print(f"Indexing Markdown: {file_path}")
            self.documents[doc_id] = {
                'id': doc_id,
                'type': 'md',
                'path': file_path,
                'doc_name': os.path.basename(file_path),
                'doc_description': '',
                'line_count': 0,
                'structure': [],
            }
        else:
            raise ValueError(f"Unsupported file format for: {file_path}")

        print(f"Indexing complete. Document ID: {doc_id}")
        if self.workspace:
            self._save_doc(doc_id)
        return doc_id

    @staticmethod
    def _make_meta_entry(doc: dict) -> dict:
        """从文档字典构建轻量级元条目"""
        entry = {
            'type': doc.get('type', ''),
            'doc_name': doc.get('doc_name', ''),
            'doc_description': doc.get('doc_description', ''),
            'path': doc.get('path', ''),
        }
        if doc.get('type') == 'pdf':
            entry['page_count'] = doc.get('page_count')
        elif doc.get('type') == 'md':
            entry['line_count'] = doc.get('line_count')
        return entry

    @staticmethod
    def _read_json(path) -> dict | None:
        """读取 JSON 文件，出错时返回 None"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: corrupt {Path(path).name}: {e}")
            return None

    def _save_doc(self, doc_id: str):
        """保存文档到工作空间"""
        doc = self.documents[doc_id].copy()
        if doc.get('structure') and doc.get('type') == 'pdf':
            doc['structure'] = remove_fields(doc['structure'], fields=['text'])
        path = self.workspace / f"{doc_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        self._save_meta(doc_id, self._make_meta_entry(doc))
        self.documents[doc_id].pop('structure', None)
        self.documents[doc_id].pop('pages', None)

    def _rebuild_meta(self) -> dict:
        """扫描文档 JSON 文件并返回元数据字典"""
        meta = {}
        for path in self.workspace.glob("*.json"):
            if path.name == META_INDEX:
                continue
            doc = self._read_json(path)
            if doc and isinstance(doc, dict):
                meta[path.stem] = self._make_meta_entry(doc)
        return meta

    def _read_meta(self) -> dict | None:
        """读取并验证 _meta.json"""
        meta = self._read_json(self.workspace / META_INDEX)
        if meta is not None and not isinstance(meta, dict):
            print(f"Warning: {META_INDEX} is not a JSON object, ignoring")
            return None
        return meta

    def _save_meta(self, doc_id: str, entry: dict):
        """保存元数据"""
        meta = self._read_meta() or self._rebuild_meta()
        meta[doc_id] = entry
        meta_path = self.workspace / META_INDEX
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def _load_workspace(self):
        """从 _meta.json 加载文档列表"""
        meta = self._read_meta()
        if meta is None:
            meta = self._rebuild_meta()
            if meta:
                print(f"Loaded {len(meta)} document(s) from workspace (legacy mode).")
        for doc_id, entry in meta.items():
            doc = dict(entry, id=doc_id)
            if doc.get('path') and not os.path.isabs(doc['path']):
                doc['path'] = str((self.workspace / doc['path']).resolve())
            # 从 path 中提取实际文件名（如 西游记_index.json）
            if doc.get('path'):
                doc['_filename'] = os.path.basename(doc['path'])
            self.documents[doc_id] = doc

    def _ensure_doc_loaded(self, doc_id: str):
        """按需加载完整文档 JSON（structure, pages 等）"""
        doc = self.documents.get(doc_id)
        if not doc or doc.get('structure') is not None:
            return
        filename = doc.get('_filename') or f"{doc_id}.json"
        filepath = self.workspace / filename
        print(f"[PageIndex] Loading doc {doc_id} from {filepath}")
        full = self._read_json(filepath)
        if not full:
            return
        doc['structure'] = full.get('structure', [])
        if full.get('pages'):
            doc['pages'] = full['pages']

    def get_document(self, doc_id: str) -> str:
        """返回文档元数据 JSON"""
        from .retrieve import get_document as _get_document
        return _get_document(self.documents, doc_id)

    def get_document_structure(self, doc_id: str) -> str:
        """返回文档树结构 JSON（不含 text 字段）"""
        if self.workspace:
            self._ensure_doc_loaded(doc_id)
        from .retrieve import get_document_structure as _get_document_structure
        return _get_document_structure(self.documents, doc_id)

    def get_page_content(self, doc_id: str, pages: str) -> str:
        """返回指定页码的内容（如 '5-7', '3,8', '12'）"""
        if self.workspace:
            self._ensure_doc_loaded(doc_id)
        from .retrieve import get_page_content as _get_page_content
        return _get_page_content(self.documents, doc_id, pages)

    def list_documents(self) -> list[dict]:
        """列出工作空间中的所有文档"""
        return [
            {
                'doc_id': doc_id,
                'doc_name': doc.get('doc_name', ''),
                'type': doc.get('type', ''),
                'doc_description': doc.get('doc_description', ''),
            }
            for doc_id, doc in self.documents.items()
        ]