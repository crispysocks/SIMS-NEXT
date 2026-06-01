import { describe, it, expect, vi, beforeEach } from 'vitest';
import { studentsApi } from '../students';

describe('studentsApi.list', () => {
  beforeEach(() => { vi.restoreAllMocks(); });

  it('builds URL with all params', async () => {
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, page: 2, page_size: 10 }), { status: 200 })
    );
    await studentsApi.list({ page: 2, page_size: 10, name: '张', student_no: 'S001' });
    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/v1/students?page=2&page_size=10&name=%E5%BC%A0&student_no=S001',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('skips empty params', async () => {
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 20 }), { status: 200 })
    );
    await studentsApi.list({ page: 1 });
    expect(fetchSpy).toHaveBeenCalledWith('/api/v1/students?page=1', expect.anything());
  });
});
