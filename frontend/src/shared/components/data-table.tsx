import { useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { TableSkeleton } from './loading';
import { EmptyState } from './empty-state';
import { cn } from '@/lib/utils';

export interface DataTableColumn<T> {
  key: keyof T | string;
  header: string;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (row: T) => React.ReactNode;
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  loading?: boolean;
  searchable?: boolean;
  searchKeys?: (keyof T)[];
  pageSize?: number;
  emptyTitle?: string;
  emptyDescription?: string;
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  loading,
  searchable,
  searchKeys,
  pageSize = 10,
  emptyTitle = '暂无数据',
  emptyDescription,
  rowKey,
  onRowClick,
}: DataTableProps<T>) {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const filtered = searchable && search
    ? data.filter((row) =>
        (searchKeys ?? (Object.keys(row) as (keyof T)[])).some((k) =>
          String(row[k]).toLowerCase().includes(search.toLowerCase())
        )
      )
    : data;

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const paged = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="space-y-3">
      {searchable && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="搜索..."
            className="w-full h-9 pl-9 pr-3 rounded-md bg-[var(--surface)] border border-[var(--border)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
          />
        </div>
      )}

      <div className="rounded-lg border border-[var(--border)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[var(--surface-2)] text-[var(--text-muted)]">
              <tr>
                {columns.map((c) => (
                  <th key={String(c.key)} style={{ width: c.width }} className={cn('text-left font-medium px-4 py-2.5', c.align === 'right' && 'text-right', c.align === 'center' && 'text-center')}>
                    {c.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={columns.length} className="p-4"><TableSkeleton rows={5} cols={columns.length} /></td></tr>
              ) : paged.length === 0 ? (
                <tr><td colSpan={columns.length}><EmptyState title={emptyTitle} description={emptyDescription} /></td></tr>
              ) : (
                paged.map((row) => (
                  <tr
                    key={rowKey(row)}
                    onClick={() => onRowClick?.(row)}
                    className={cn('border-t border-[var(--border)] hover:bg-[var(--surface-2)]/50', onRowClick && 'cursor-pointer')}
                  >
                    {columns.map((c) => (
                      <td key={String(c.key)} className={cn('px-4 py-3 text-[var(--text)]', c.align === 'right' && 'text-right', c.align === 'center' && 'text-center')}>
                        {c.render ? c.render(row) : String(row[c.key as keyof T] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {filtered.length > pageSize && (
        <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
          <span>共 {filtered.length} 条，第 {page} / {totalPages} 页</span>
          <div className="flex gap-1">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="p-1 rounded hover:bg-[var(--surface-2)] disabled:opacity-40">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="p-1 rounded hover:bg-[var(--surface-2)] disabled:opacity-40">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
