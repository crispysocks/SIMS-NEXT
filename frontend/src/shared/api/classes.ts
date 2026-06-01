import { api } from '@/lib/api';

// 1:1 mirror of backend Pydantic `ClassDetail` schema
// (app/schemas/class_schema.py). Keep field names in sync with the backend.
// Note: the backend does not currently denormalize the head teacher's name
// on this endpoint — we only expose `head_teacher_no` as an FK string.
export interface Class {
  id: number;
  class_no: string;
  class_name: string;
  head_teacher_no: string;
  created_at: string;
  updated_at: string;
  [key: string]: unknown;
}

// The classes list endpoint returns all rows in one shot (no server-side
// pagination), so we model the list shape as a flat array of items.
export type ClassList = Class[];

export interface ClassQuery {
  class_name?: string;
  class_no?: string;
  head_teacher_no?: string;
}

// Build a `?a=1&b=2` query string from a partial query object. Skips
// `undefined` / empty / null values. Insertion order is preserved.
function buildQuery(q: ClassQuery): string {
  const params = new URLSearchParams();
  if (q.class_no) params.append('class_no', q.class_no);
  if (q.class_name) params.append('class_name', q.class_name);
  if (q.head_teacher_no) params.append('head_teacher_no', q.head_teacher_no);
  const s = params.toString();
  return s ? `?${s}` : '';
}

export interface ClassCreate {
  class_no: string;
  class_name: string;
  head_teacher_no: string;
}

export type ClassUpdate = Partial<ClassCreate>;

export const classesApi = {
  list: (q: ClassQuery = {}) => api.get<ClassList>(`/classes${buildQuery(q)}`),
  get: (class_no: string) => api.get<Class>(`/classes/${class_no}`),
  create: (data: ClassCreate) => api.post<Class>('/classes', data),
  update: (class_no: string, data: ClassUpdate) =>
    api.put<Class>(`/classes/${class_no}`, data),
  remove: (class_no: string) => api.delete(`/classes/${class_no}`),
};
