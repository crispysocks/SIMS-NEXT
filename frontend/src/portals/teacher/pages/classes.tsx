import { PageHeader } from '@/shared/components/page-header';
import { DataTable, type DataTableColumn } from '@/shared/components/data-table';
import { Button } from '@/components/ui/button';

interface Class { id: string; class_no: string; name: string; head_teacher: string; }

const COLUMNS: DataTableColumn<Class>[] = [
  { key: 'class_no', header: '班级编号', width: '120px' },
  { key: 'name', header: '班级名称', width: '160px' },
  { key: 'head_teacher', header: '班主任' },
];

const MOCK: Class[] = [
  { id: '1', class_no: 'C001', name: '高一(1)班', head_teacher: '王老师' },
  { id: '2', class_no: 'C002', name: '高一(2)班', head_teacher: '李老师' },
  { id: '3', class_no: 'C003', name: '高一(3)班', head_teacher: '赵老师' },
];

export function Classes() {
  return (
    <div className="space-y-6">
      <PageHeader title="班级管理" description="全校班级信息" actions={<Button>新增班级</Button>} />
      <DataTable columns={COLUMNS} data={MOCK} searchable rowKey={(r) => r.id} />
    </div>
  );
}
