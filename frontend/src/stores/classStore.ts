import { create } from 'zustand';
import { api } from '@/lib/api';

export interface Class {
  id: number;
  class_no: string;
  class_name: string;
  head_teacher_no: string;
  created_at: string;
  updated_at: string;
}

interface ClassState {
  classes: Class[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: string | null;
  modalOpen: boolean;
  editingClass: Class | null;
  searchClassNo: string;
  searchClassName: string;
  fetchClasses: () => Promise<void>;
  setPage: (page: number) => void;
  setSearchClassNo: (no: string) => void;
  setSearchClassName: (name: string) => void;
  openModal: (cls?: Class) => void;
  closeModal: () => void;
  createClass: (data: Omit<Class, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  updateClass: (class_id: number, data: Partial<Class>) => Promise<void>;
  deleteClass: (class_id: number) => Promise<void>;
}

export const useClassStore = create<ClassState>()((set, get) => ({
  classes: [],
  total: 0,
  page: 1,
  pageSize: 20,
  loading: false,
  error: null,
  modalOpen: false,
  editingClass: null,
  searchClassNo: '',
  searchClassName: '',

  fetchClasses: async () => {
    const { searchClassNo, searchClassName, page, pageSize } = get();
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (searchClassNo) params.append('class_no', searchClassNo);
      if (searchClassName) params.append('class_name', searchClassName);
      const data = await api.get<{ items: Class[]; total: number }>(`/classes?${params}`);
      set({ classes: data.items, total: data.total, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取班级列表失败', loading: false });
    }
  },

  setPage: (page) => {
    set({ page });
    get().fetchClasses();
  },
  setSearchClassNo: (searchClassNo) => {
    set({ searchClassNo, page: 1 });
    get().fetchClasses();
  },
  setSearchClassName: (searchClassName) => {
    set({ searchClassName, page: 1 });
    get().fetchClasses();
  },

  openModal: (cls) => set({ modalOpen: true, editingClass: cls || null }),
  closeModal: () => set({ modalOpen: false, editingClass: null }),

  createClass: async (data) => {
    await api.post('/classes', data);
    await get().fetchClasses();
    get().closeModal();
  },

  updateClass: async (class_id, data) => {
    await api.put(`/classes/${class_id}`, data);
    await get().fetchClasses();
    get().closeModal();
  },

  deleteClass: async (class_id) => {
    await api.delete(`/classes/${class_id}`);
    await get().fetchClasses();
  },
}));