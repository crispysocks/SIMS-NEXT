import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/shared/components/page-header';
import { DataTable, type DataTableColumn } from '@/shared/components/data-table';
import { SectionErrorBoundary } from '@/shared/components/error-boundary';
import { TableSkeleton } from '@/shared/components/loading';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { scoresApi, type Score } from '@/shared/api/scores';

const COLUMNS: DataTableColumn<Score>[] = [
  { key: 'student_no', header: '学号', width: '120px' },
  { key: 'student_name', header: '姓名', width: '120px' },
  { key: 'exam_name', header: '考试', width: '160px' },
  { key: 'score', header: '成绩', width: '100px', align: 'right' },
];

// Backend has no server-side pagination for scores, so we load all rows
// matching the current query and paginate client-side.
const PAGE_SIZE = 20;

export function Scores() {
  const [search, setSearch] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['scores', { search }],
    queryFn: () => scoresApi.list(),
  });

  const rows = data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="成绩管理" description="全校学生考试成绩" actions={<Button>录入成绩</Button>} />

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
            searchKeys={['student_no', 'student_name', 'exam_name']}
            rowKey={(r) => String(r.id)}
          />
        )}
      </SectionErrorBoundary>
    </div>
  );
}
