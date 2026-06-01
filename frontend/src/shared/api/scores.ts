import { api } from '@/lib/api';

// 1:1 mirror of backend Pydantic `ScoreDetail` schema
// (app/schemas/score_schema.py). Keep field names in sync with the backend.
export interface Score {
  id: number;
  student_no: string;
  student_name: string;
  exam_name: string;
  score: number;
  created_at: string;
  updated_at: string;
  [key: string]: unknown;
}

// The scores list endpoint returns all matching rows in one shot — no
// server-side pagination, no `page`/`page_size` fields in the response.
export type ScoreList = Score[];

export interface ScoreQuery {
  student_no?: string;
  student_name?: string;
  exam_name?: string;
}

// Build a `?a=1&b=2` query string from a partial query object. Skips
// `undefined` / empty / null values. Insertion order is preserved.
function buildQuery(q: ScoreQuery): string {
  const params = new URLSearchParams();
  if (q.student_no) params.append('student_no', q.student_no);
  if (q.student_name) params.append('student_name', q.student_name);
  if (q.exam_name) params.append('exam_name', q.exam_name);
  const s = params.toString();
  return s ? `?${s}` : '';
}

export interface ScoreCreate {
  student_no: string;
  exam_name: string;
  score: number;
}

export type ScoreUpdate = Partial<ScoreCreate>;

export const scoresApi = {
  list: (q: ScoreQuery = {}) => api.get<ScoreList>(`/scores${buildQuery(q)}`),
  get: (id: number) => api.get<Score>(`/scores/${id}`),
  create: (data: ScoreCreate) => api.post<Score>('/scores', data),
  update: (id: number, data: ScoreUpdate) =>
    api.put<Score>(`/scores/${id}`, data),
  remove: (id: number) => api.delete(`/scores/${id}`),
};
