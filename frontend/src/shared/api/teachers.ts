import { api } from '@/lib/api';

// 1:1 mirror of backend Pydantic `TeacherDetail` schema
// (app/schemas/teacher.py). Keep field names in sync with the backend.
export interface Teacher {
  id: number;
  teacher_no: string;
  name: string;
  gender: string;
  entry_date: string;
  created_at: string;
  updated_at: string;
  [key: string]: unknown;
}

// 1:1 mirror of `PaginatedTeachers`. Used by server-driven lists.
export interface PaginatedTeachers {
  items: Teacher[];
  total: number;
  page: number;
  page_size: number;
}

export interface TeacherQuery {
  page?: number;
  page_size?: number;
  name?: string;
  teacher_no?: string;
  gender?: string;
}

// Build a `?a=1&b=2` query string from a partial query object. Skips
// `undefined` / empty / null values. Insertion order is preserved so the
// resulting URL is stable and predictable.
function buildQuery(q: TeacherQuery): string {
  const params = new URLSearchParams();
  if (q.page !== undefined) params.append('page', String(q.page));
  if (q.page_size !== undefined) params.append('page_size', String(q.page_size));
  if (q.name) params.append('name', q.name);
  if (q.teacher_no) params.append('teacher_no', q.teacher_no);
  if (q.gender) params.append('gender', q.gender);
  const s = params.toString();
  return s ? `?${s}` : '';
}

export interface TeacherCreate {
  teacher_no: string;
  name: string;
  gender: string;
  entry_date: string;
}

export type TeacherUpdate = Partial<TeacherCreate>;

export const teachersApi = {
  list: (q: TeacherQuery = {}) => api.get<PaginatedTeachers>(`/teachers${buildQuery(q)}`),
  get: (teacher_no: string) => api.get<Teacher>(`/teachers/${teacher_no}`),
  create: (data: TeacherCreate) => api.post<Teacher>('/teachers', data),
  update: (teacher_no: string, data: TeacherUpdate) =>
    api.put<Teacher>(`/teachers/${teacher_no}`, data),
  remove: (teacher_no: string) => api.delete<void>(`/teachers/${teacher_no}`),
};
