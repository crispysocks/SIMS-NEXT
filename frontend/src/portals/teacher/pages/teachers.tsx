import { PageHeader } from '@/shared/components/page-header';
import { DataTable, type DataTableColumn } from '@/shared/components/data-table';
import { Button } from '@/components/ui/button';

interface Teacher { id: string; teacher_no: string; name: string; gender: string; joined_at: string; }

const COLUMNS: DataTableColumn<Teacher>[] = [
  { key: 'teacher_no', header: '工号', width: '120px' },
  { key: 'name', header: '姓名', width: '120px' },
  { key: 'gender', header: '性别', width: '80px' },
  { key: 'joined_at', header: '入职时间' },
];

const MOCK: Teacher[] = [
  { id: '1', teacher_no: 'T001', name: '王老师', gender: '男', joined_at: '2018-09-01' },
  { id: '2', teacher_no: 'T002', name: '李老师', gender: '女', joined_at: '2020-03-15' },
];

export function Teachers() {
  return (
    <div className="space-y-6">
      <PageHeader title="教师管理" description="全校教师信息" actions={<Button>新增教师</Button>} />
      <DataTable columns={COLUMNS} data={MOCK} searchable rowKey={(r) => r.id} />
    </div>
  );
}
