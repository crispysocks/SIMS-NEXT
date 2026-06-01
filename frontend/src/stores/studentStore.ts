import { create } from 'zustand';
import { api } from '@/lib/api';

export interface Student {
  id: number;
  student_no: string;
  name: string;
  gender: string;
  age: number;
  native_place?: string;
  class_id?: number;
  enrollment_date: string;
  created_at: string;
  updated_at: string;
}

interface StudentState {
  students: Student[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: string | null;
  modalOpen: boolean;
  editingStudent: Student | null;
  searchName: string;
  searchStudentNo: string;
  fetchStudents: () => Promise<void>;
  setPage: (page: number) => void;
  setSearchName: (name: string) => void;
  setSearchStudentNo: (no: string) => void;
  openModal: (student?: Student) => void;
  closeModal: () => void;
  createStudent: (data: Omit<Student, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  updateStudent: (student_no: string, data: Partial<Student>) => Promise<void>;
  deleteStudent: (student_no: string) => Promise<void>;
}

export const useStudentStore = create<StudentState>()((set, get) => ({
  students: [],
  total: 0,
  page: 1,
  pageSize: 20,
  loading: false,
  error: null,
  modalOpen: false,
  editingStudent: null,
  searchName: '',
  searchStudentNo: '',

  fetchStudents: async () => {
    const { searchName, searchStudentNo, page, pageSize } = get();
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (searchName) params.append('name', searchName);
      if (searchStudentNo) params.append('student_no', searchStudentNo);
      const data = await api.get<{ items: Student[]; total: number }>(`/students?${params}`);
      set({ students: data.items, total: data.total, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取学生列表失败', loading: false });
    }
  },

  setPage: (page) => {
    set({ page });
    get().fetchStudents();
  },
  setSearchName: (searchName) => {
    set({ searchName, page: 1 });
    get().fetchStudents();
  },
  setSearchStudentNo: (searchStudentNo) => {
    set({ searchStudentNo, page: 1 });
    get().fetchStudents();
  },

  openModal: (student) => set({ modalOpen: true, editingStudent: student || null }),
  closeModal: () => set({ modalOpen: false, editingStudent: null }),

  createStudent: async (data) => {
    await api.post('/students', data);
    await get().fetchStudents();
    get().closeModal();
  },

  updateStudent: async (student_no, data) => {
    await api.put(`/students/${student_no}`, data);
    await get().fetchStudents();
    get().closeModal();
  },

  deleteStudent: async (student_no) => {
    await api.delete(`/students/${student_no}`);
    await get().fetchStudents();
  },
}));