import { create } from 'zustand';
import { api } from '@/lib/api';
import { useAuthStore } from './authStore';

export interface Question {
  id: string;
  subject: string;
  topic: string;
  difficulty: string;
  question_text: string;
  knowledge_tags: string[];
  learning_objectives: string[];
}

export interface TutorResponse {
  explanation: string;
  hint: string;
  encouragement: string;
}

export interface Diagnosis {
  error_types: string[];
  diagnosis_labels: string[];
  confidence: number;
}

export interface Remediation {
  recommended_topics: string[];
  retrieval_tags: string[];
}

export interface TutoringExplanation {
  what_is_wrong: string;
  why_it_is_wrong: string;
  how_to_fix: string;
  similar_examples: string[];
  retrieved_context: string;
  generation_source?: string;
  metadata: Record<string, unknown>;
}

export interface KnowledgeSnippet {
  id: string;
  title: string;
  topic: string;
  tags: string[];
  diagnosis_labels: string[];
  score?: number;
  metadata: Record<string, unknown>;
}

export interface AnswerResult {
  is_correct: boolean;
  correct_answer: string;
  student_answer: string;
  topic: string;
  tutor_response?: TutorResponse;
  diagnosis?: Diagnosis;
  remediation?: Remediation;
  explanation?: TutoringExplanation;
  retrieved_snippets: KnowledgeSnippet[];
}

export interface HintResponse {
  hint: string;
  level: number;
  remaining: number;
}

export interface MasteryState {
  topic_id: string;
  alpha: number;
  beta: number;
  total_attempts: number;
  correct_attempts: number;
  last_seen?: string;
  mastery: number;
  variance: number;
}

export interface Progress {
  mastery_states: MasteryState[];
  total_questions: number;
  correct_count: number;
  accuracy: number;
  correct_streak: number;
  wrong_streak: number;
}

export interface SubjectInfo {
  subject: string;
  available_subjects: string[];
}

interface TutorState {
  currentQuestion: Question | null;
  answerResult: AnswerResult | null;
  hint: HintResponse | null;
  progress: Progress | null;
  subjectInfo: SubjectInfo | null;
  loading: boolean;
  submitting: boolean;
  error: string | null;
  fetchQuestion: () => Promise<void>;
  submitAnswer: (answer: string) => Promise<void>;
  requestHint: () => Promise<void>;
  fetchProgress: () => Promise<void>;
  fetchSubject: () => Promise<void>;
  switchSubject: (subject: string) => Promise<void>;
  resetSession: () => Promise<void>;
  clearResult: () => void;
}

export const useTutorStore = create<TutorState>((set, get) => ({
  currentQuestion: null,
  answerResult: null,
  hint: null,
  progress: null,
  subjectInfo: null,
  loading: false,
  submitting: false,
  error: null,

  fetchSubject: async () => {
    try {
      const token = useAuthStore.getState().token;
      const data = await api.get<SubjectInfo>('/tutor/subject', token);
      set({ subjectInfo: data });
    } catch (err) {
      console.error('获取学科信息失败:', err);
    }
  },

  switchSubject: async (subject: string) => {
    try {
      const token = useAuthStore.getState().token;
      const data = await api.post<SubjectInfo>('/tutor/subject', { subject }, token);
      set({
        subjectInfo: data,
        currentQuestion: null,
        answerResult: null,
        hint: null,
        progress: null,
      });
      // 重新获取题目和进度
      get().fetchQuestion();
      get().fetchProgress();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '切换学科失败' });
    }
  },

  fetchQuestion: async () => {
    set({ loading: true, error: null, answerResult: null, hint: null });
    try {
      const token = useAuthStore.getState().token;
      const data = await api.get<Question>('/tutor/question', token);
      set({ currentQuestion: data, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取题目失败', loading: false });
    }
  },

  submitAnswer: async (answer: string) => {
    const { currentQuestion } = get();
    if (!currentQuestion) return;

    set({ submitting: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const data = await api.post<AnswerResult>('/tutor/answer', { student_answer: answer }, token);
      set({ answerResult: data, submitting: false });
      // 自动刷新进度
      get().fetchProgress();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '提交答案失败', submitting: false });
    }
  },

  requestHint: async () => {
    const { currentQuestion } = get();
    if (!currentQuestion) return;

    try {
      const token = useAuthStore.getState().token;
      const data = await api.post<HintResponse>('/tutor/hint', {}, token);
      set({ hint: data });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取提示失败' });
    }
  },

  fetchProgress: async () => {
    try {
      const token = useAuthStore.getState().token;
      const data = await api.get<Progress>('/tutor/progress', token);
      set({ progress: data });
    } catch (err) {
      console.error('获取进度失败:', err);
    }
  },

  resetSession: async () => {
    try {
      const token = useAuthStore.getState().token;
      await api.post('/tutor/reset', {}, token);
      set({
        currentQuestion: null,
        answerResult: null,
        hint: null,
        progress: null,
      });
      // 重新获取题目
      get().fetchQuestion();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '重置失败' });
    }
  },

  clearResult: () => set({ answerResult: null, hint: null }),
}));
