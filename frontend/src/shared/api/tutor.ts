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

// 1:1 mirror of backend `AnswerResult` (app/schemas/tutor.py). The backend
// does not have an `options` field on the question. The UI synthesizes an
// A/B/C/D option set so the existing multiple-choice QuestionCard still
// renders. The chosen option letter is sent as `student_answer` to the
// backend, which compares it to the actual text answer returned in
// `correct_answer`.
export interface TutorResponseOut {
  explanation: string;
  hint: string;
  encouragement: string;
}

export interface DiagnosisResultOut {
  error_types: string[];
  diagnosis_labels: string[];
  confidence: number;
}

export interface RemediationPlanOut {
  recommended_topics: string[];
  retrieval_tags: string[];
}

export interface TutoringExplanationOut {
  what_is_wrong: string;
  why_it_is_wrong: string;
  how_to_fix: string;
  similar_examples: string[];
  retrieved_context: string;
  generation_source?: string | null;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeSnippetOut {
  id: string;
  title: string;
  topic: string;
  tags: string[];
  diagnosis_labels: string[];
  score: number;
  metadata?: Record<string, unknown>;
}

export interface SubmitResult {
  is_correct: boolean;
  correct_answer: string;
  student_answer: string;
  topic: string;
  tutor_response: TutorResponseOut | null;
  diagnosis: DiagnosisResultOut | null;
  remediation: RemediationPlanOut | null;
  explanation: TutoringExplanationOut | null;
  retrieved_snippets: KnowledgeSnippetOut[];
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
