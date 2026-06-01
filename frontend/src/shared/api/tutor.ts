import { api } from '@/lib/api';

// 1:1 mirror of backend Pydantic schemas in `app/schemas/tutor.py` and the
// response models defined in `app/api/v1/tutor_router.py`.
// Field names kept in sync with the backend.

export interface Question {
  id: string;
  subject: string;
  topic: string;
  difficulty: string;
  question_text: string;
  knowledge_tags: string[];
  learning_objectives: string[];
}

// Backend has no `options` field on the question. The UI synthesizes an
// A/B/C/D option set so the existing multiple-choice QuestionCard still
// renders. The chosen option letter is sent as `student_answer` to the
// backend, which compares it to the actual text answer returned in
// `AnswerResult.correct_answer`.
export interface SubmitResult {
  is_correct: boolean;
  correct_answer: string;
  student_answer: string;
  topic: string;
  explanation: string;
  hint?: string | null;
  encouragement?: string | null;
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
  last_seen: string | null;
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

export const tutorApi = {
  getNextQuestion: () => api.get<Question>('/tutor/question'),

  // The backend's `AnswerSubmission` is just `{ student_answer: string }`.
  // We accept an `optionId` from the UI and forward it as `student_answer`.
  submitAnswer: (data: { optionId: string }) =>
    api.post<SubmitResult>('/tutor/answer', { student_answer: data.optionId }),

  requestHint: () => api.post<HintResponse>('/tutor/hint', {}),

  getMastery: () => api.get<MasteryState[]>('/tutor/mastery'),

  getProgress: () => api.get<Progress>('/tutor/progress'),

  getSubject: () => api.get<SubjectInfo>('/tutor/subject'),

  switchSubject: (subject: string) =>
    api.post<SubjectInfo>('/tutor/subject', { subject }),

  reset: () => api.post<{ status: string }>('/tutor/reset', {}),
};
