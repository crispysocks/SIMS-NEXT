import { create } from 'zustand';
import { api } from '@/lib/api';
import { useAuthStore } from '@/shared/stores/auth-store';

export interface Teacher {
  id: number;
  teacher_no: string;
  name: string;
  gender: string;
  entry_date: string;
  created_at: string;
  updated_at: string;
}

interface TeacherState {
  teachers: Teacher[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: string | null;
  modalOpen: boolean;
  editingTeacher: Teacher | null;
  searchName: string;
  searchTeacherNo: string;
  fetchTeachers: () => Promise<void>;
  setPage: (page: number) => void;
  setSearchName: (name: string) => void;
  setSearchTeacherNo: (no: string) => void;
  openModal: (teacher?: Teacher) => void;
  closeModal: () => void;
  createTeacher: (data: Omit<Teacher, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  updateTeacher: (teacher_no: string, data: Partial<Teacher>) => Promise<void>;
  deleteTeacher: (teacher_no: string) => Promise<void>;
}

export const useTeacherStore = create<TeacherState>((set, get) => ({
  teachers: [],
  total: 0,
  page: 1,
  pageSize: 20,
  loading: false,
  error: null,
  modalOpen: false,
  editingTeacher: null,
  searchName: '',
  searchTeacherNo: '',

  fetchTeachers: async () => {
    const { searchName, searchTeacherNo, page, pageSize } = get();
    set({ loading: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (searchName) params.append('name', searchName);
      if (searchTeacherNo) params.append('teacher_no', searchTeacherNo);
      const data = await api.get<{ items: Teacher[]; total: number }>(`/teachers?${params}`, token);
      set({ teachers: data.items, total: data.total, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取教师列表失败', loading: false });
    }
  },

  setPage: (page) => set({ page }, () => get().fetchTeachers()),
  setSearchName: (searchName) => set({ searchName, page: 1 }, () => get().fetchTeachers()),
  setSearchTeacherNo: (searchTeacherNo) => set({ searchTeacherNo, page: 1 }, () => get().fetchTeachers()),

  openModal: (teacher) => set({ modalOpen: true, editingTeacher: teacher || null }),
  closeModal: () => set({ modalOpen: false, editingTeacher: null }),

  createTeacher: async (data) => {
    const token = useAuthStore.getState().token;
    await api.post('/teachers', data, token);
    await get().fetchTeachers();
    get().closeModal();
  },

  updateTeacher: async (teacher_no, data) => {
    const token = useAuthStore.getState().token;
    await api.put(`/teachers/${teacher_no}`, data, token);
    await get().fetchTeachers();
    get().closeModal();
  },

  deleteTeacher: async (teacher_no) => {
    const token = useAuthStore.getState().token;
    await api.delete(`/teachers/${teacher_no}`, token);
    await get().fetchTeachers();
  },
}));