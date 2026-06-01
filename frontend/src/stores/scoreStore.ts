import { create } from 'zustand';
import { api } from '@/lib/api';

export interface Score {
  id: number;
  student_no: string;
  student_name: string;
  exam_name: string;
  score: number;
  created_at: string;
  updated_at: string;
}

interface ScoreState {
  scores: Score[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: string | null;
  modalOpen: boolean;
  editingScore: Score | null;
  searchStudentNo: string;
  searchExamName: string;
  searchStudentName: string;
  fetchScores: () => Promise<void>;
  setPage: (page: number) => void;
  setSearchStudentNo: (no: string) => void;
  setSearchExamName: (name: string) => void;
  setSearchStudentName: (name: string) => void;
  openModal: (score?: Score) => void;
  closeModal: () => void;
  createScore: (data: Omit<Score, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  updateScore: (score_id: number, data: Partial<Score>) => Promise<void>;
  deleteScore: (score_id: number) => Promise<void>;
}

export const useScoreStore = create<ScoreState>()((set, get) => ({
  scores: [],
  total: 0,
  page: 1,
  pageSize: 20,
  loading: false,
  error: null,
  modalOpen: false,
  editingScore: null,
  searchStudentNo: '',
  searchExamName: '',
  searchStudentName: '',

  fetchScores: async () => {
    const { searchStudentNo, searchExamName, searchStudentName, page, pageSize } = get();
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (searchStudentNo) params.append('student_no', searchStudentNo);
      if (searchExamName) params.append('exam_name', searchExamName);
      if (searchStudentName) params.append('student_name', searchStudentName);
      const data = await api.get<{ items: Score[]; total: number }>(`/scores?${params}`);
      set({ scores: data.items, total: data.total, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取成绩列表失败', loading: false });
    }
  },

  setPage: (page) => {
    set({ page });
    get().fetchScores();
  },
  setSearchStudentNo: (searchStudentNo) => {
    set({ searchStudentNo, page: 1 });
    get().fetchScores();
  },
  setSearchExamName: (searchExamName) => {
    set({ searchExamName, page: 1 });
    get().fetchScores();
  },
  setSearchStudentName: (searchStudentName) => {
    set({ searchStudentName, page: 1 });
    get().fetchScores();
  },

  openModal: (score) => set({ modalOpen: true, editingScore: score || null }),
  closeModal: () => set({ modalOpen: false, editingScore: null }),

  createScore: async (data) => {
    await api.post('/scores', data);
    await get().fetchScores();
    get().closeModal();
  },

  updateScore: async (score_id, data) => {
    await api.put(`/scores/${score_id}`, data);
    await get().fetchScores();
    get().closeModal();
  },

  deleteScore: async (score_id) => {
    await api.delete(`/scores/${score_id}`);
    await get().fetchScores();
  },
}));