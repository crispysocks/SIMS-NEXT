import { PageHeader } from '@/shared/components/page-header';
import { DataTable, type DataTableColumn } from '@/shared/components/data-table';
import { Button } from '@/components/ui/button';

interface Score { id: string; student_no: string; exam: string; score: number; }

const COLUMNS: DataTableColumn<Score>[] = [
  { key: 'student_no', header: '学号', width: '120px' },
  { key: 'exam', header: '考试', width: '160px' },
  { key: 'score', header: '成绩', width: '100px', align: 'right' },
];

const MOCK: Score[] = [
  { id: '1', student_no: 'S001', exam: '月考1', score: 85 },
  { id: '2', student_no: 'S001', exam: '月考2', score: 88 },
  { id: '3', student_no: 'S002', exam: '月考1', score: 92 },
];

export function Scores() {
  return (
    <div className="space-y-6">
      <PageHeader title="成绩管理" description="全校学生考试成绩" actions={<Button>录入成绩</Button>} />
      <DataTable columns={COLUMNS} data={MOCK} searchable rowKey={(r) => r.id} />
    </div>
  );
}
