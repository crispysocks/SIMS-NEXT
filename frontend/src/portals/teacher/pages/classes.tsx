import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/shared/components/page-header';
import { DataTable, type DataTableColumn } from '@/shared/components/data-table';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';
import { TableSkeleton } from '@/shared/components/loading';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { classesApi, type Class } from '@/shared/api/classes';

const COLUMNS: DataTableColumn<Class>[] = [
  { key: 'class_no', header: '班级编号', width: '120px' },
  { key: 'class_name', header: '班级名称', width: '160px' },
  { key: 'head_teacher_no', header: '班主任工号' },
];

// Backend has no server-side pagination for classes, so we load everything
// and let the DataTable paginate client-side.
const PAGE_SIZE = 20;

export function Classes() {
  const [search, setSearch] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['classes', { search }],
    queryFn: () => classesApi.list(),
  });

  const rows = data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="班级管理" description="全校班级信息" actions={<Button>新增班级</Button>} />

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
            data={rows}
            searchable
            searchQuery={search}
            onSearch={setSearch}
            pageSize={PAGE_SIZE}
            searchKeys={['class_no', 'class_name', 'head_teacher_no']}
            rowKey={(r) => String(r.id)}
          />
        )}
      </SectionErrorBoundary>
    </div>
  );
}
