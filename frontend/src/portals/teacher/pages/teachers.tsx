import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/shared/components/page-header';
import { DataTable, type DataTableColumn } from '@/shared/components/data-table';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';
import { TableSkeleton } from '@/shared/components/loading';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { teachersApi, type Teacher } from '@/shared/api/teachers';

const COLUMNS: DataTableColumn<Teacher>[] = [
  { key: 'teacher_no', header: '工号', width: '120px' },
  { key: 'name', header: '姓名', width: '120px' },
  { key: 'gender', header: '性别', width: '80px' },
  { key: 'entry_date', header: '入职时间' },
];

const PAGE_SIZE = 10;

export function Teachers() {
  const [page, setPage] = useState(1);
  const [name, setName] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['teachers', { page, name }],
    queryFn: () => teachersApi.list({ page, page_size: PAGE_SIZE, name: name || undefined }),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="教师管理" description="全校教师信息" actions={<Button>新增教师</Button>} />

      <SectionErrorBoundary>
        {isLoading ? (
          <Card>
            <CardContent className="p-4">
              <TableSkeleton rows={8} cols={COLUMNS.length} />
            </CardContent>
          </Card>
        ) : isError ? (
          <Card>
            <CardContent className="p-6 text-center">
              <p className="text-sm text-[var(--text-muted)] mb-3">加载失败：{String((error as Error)?.message ?? error)}</p>
              <Button variant="outline" onClick={() => refetch()}>重试</Button>
            </CardContent>
          </Card>
        ) : (
          <DataTable
            columns={COLUMNS}
            data={data?.items ?? []}
            searchable
            searchQuery={name}
            onSearch={(q) => { setName(q); setPage(1); }}
            rowKey={(r) => String(r.id)}
            pagination={{
              page: data?.page ?? 1,
              pageSize: PAGE_SIZE,
              total: data?.total ?? 0,
              onChange: setPage,
            }}
          />
        )}
      </SectionErrorBoundary>
    </div>
  );
}
