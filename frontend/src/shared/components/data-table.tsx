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

export interface ServerPagination {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
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
  // Server-driven mode: when provided, data is already paged and the table
  // does NOT do client-side filtering or client-side pagination. Total and
  // current page come from the server, and the parent owns the page state.
  pagination?: ServerPagination;
  // Controlled search: when `onSearch` is provided, the search input is
  // controlled by the parent (the value of `searchQuery`) and changes are
  // reported back. The table does not maintain its own search state.
  searchQuery?: string;
  onSearch?: (query: string) => void;
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
  pagination,
  searchQuery,
  onSearch,
}: DataTableProps<T>) {
  const isServerMode = pagination !== undefined;
  const isControlledSearch = onSearch !== undefined;

  // Uncontrolled search state — only used when no `onSearch` is provided.
  const [internalSearch, setInternalSearch] = useState('');
  const search = isControlledSearch ? (searchQuery ?? '') : internalSearch;

  // Uncontrolled page state — only used when no `pagination` is provided.
  const [internalPage, setInternalPage] = useState(1);
  const currentPage = isServerMode ? pagination!.page : internalPage;

  const handleSearchChange = (value: string) => {
    if (isControlledSearch) {
      onSearch!(value);
    } else {
      setInternalSearch(value);
      setInternalPage(1);
    }
  };

  // In server mode the parent already filtered and paged the data — render as-is.
  // Otherwise (legacy client-side) we filter then paginate locally.
  const visible: T[] = isServerMode
    ? data
    : (() => {
        const filtered = searchable && search
          ? data.filter((row) =>
              (searchKeys ?? (Object.keys(row) as (keyof T)[])).some((k) =>
                String(row[k]).toLowerCase().includes(search.toLowerCase())
              )
            )
          : data;
        const start = (currentPage - 1) * pageSize;
        return filtered.slice(start, start + pageSize);
      })();

  // In server mode total comes from the pagination prop; in client mode
  // we recompute it from the filtered dataset length.
  const totalCount = isServerMode ? pagination!.total : (() => {
    const filteredCount = searchable && search
      ? data.filter((row) =>
          (searchKeys ?? (Object.keys(row) as (keyof T)[])).some((k) =>
            String(row[k]).toLowerCase().includes(search.toLowerCase())
          )
        ).length
      : data.length;
    return filteredCount;
  })();

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const showPagination = isServerMode
    ? totalCount > pageSize
    : totalCount > pageSize;

  const goToPage = (next: number) => {
    if (isServerMode) {
      pagination!.onChange(next);
    } else {
      setInternalPage(next);
    }
  };

  return (
    <div className="space-y-3">
      {searchable && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
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
              ) : visible.length === 0 ? (
                <tr><td colSpan={columns.length}><EmptyState title={emptyTitle} description={emptyDescription} /></td></tr>
              ) : (
                visible.map((row) => (
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

      {showPagination && (
        <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
          <span>共 {totalCount} 条，第 {currentPage} / {totalPages} 页</span>
          <div className="flex gap-1">
            <button onClick={() => goToPage(Math.max(1, currentPage - 1))} disabled={currentPage === 1} className="p-1 rounded hover:bg-[var(--surface-2)] disabled:opacity-40">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button onClick={() => goToPage(Math.min(totalPages, currentPage + 1))} disabled={currentPage === totalPages} className="p-1 rounded hover:bg-[var(--surface-2)] disabled:opacity-40">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
