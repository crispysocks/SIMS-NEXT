import { api } from '@/lib/api';

// 1:1 mirror of backend Pydantic `StudentDetail` schema
// (app/schemas/student.py). Keep field names in sync with the backend.
export interface Student {
  id: number;
  student_no: string;
  name: string;
  gender: string;
  age: number;
  native_place?: string | null;
  class_id?: number | null;
  enrollment_date: string;
  created_at: string;
  updated_at: string;
  [key: string]: unknown;
}

// 1:1 mirror of `PaginatedStudents`. Used by server-driven lists.
export interface PaginatedStudents {
  items: Student[];
  total: number;
  page: number;
  page_size: number;
}

export interface StudentQuery {
  page?: number;
  page_size?: number;
  name?: string;
  student_no?: string;
  class_id?: number;
}

// Build a `?a=1&b=2` query string from a partial query object. Skips
// `undefined` / empty / null values. Insertion order is preserved so the
// resulting URL is stable and predictable.
function buildQuery(q: StudentQuery): string {
  const params = new URLSearchParams();
  if (q.page !== undefined) params.append('page', String(q.page));
  if (q.page_size !== undefined) params.append('page_size', String(q.page_size));
  if (q.name) params.append('name', q.name);
  if (q.student_no) params.append('student_no', q.student_no);
  if (q.class_id !== undefined) params.append('class_id', String(q.class_id));
  const s = params.toString();
  return s ? `?${s}` : '';
}

export interface StudentCreate {
  student_no: string;
  name: string;
  gender: string;
  age: number;
  native_place?: string | null;
  class_id?: number | null;
  enrollment_date: string;
}

export type StudentUpdate = Partial<StudentCreate>;

export const studentsApi = {
  list: (q: StudentQuery = {}) => api.get<PaginatedStudents>(`/students${buildQuery(q)}`),
  get: (student_no: string) => api.get<Student>(`/students/${student_no}`),
  create: (data: StudentCreate) => api.post<Student>('/students', data),
  update: (student_no: string, data: StudentUpdate) =>
    api.put<Student>(`/students/${student_no}`, data),
  remove: (student_no: string) => api.delete<void>(`/students/${student_no}`),
};
