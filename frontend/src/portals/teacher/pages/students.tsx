import { PageHeader } from '@/shared/components/page-header';
import { DataTable, type DataTableColumn } from '@/shared/components/data-table';
import { Button } from '@/components/ui/button';

interface Student { id: string; student_no: string; name: string; gender: string; age: number; class_name: string; }

const COLUMNS: DataTableColumn<Student>[] = [
  { key: 'student_no', header: '学号', width: '120px' },
  { key: 'name', header: '姓名', width: '120px' },
  { key: 'gender', header: '性别', width: '80px' },
  { key: 'age', header: '年龄', width: '80px' },
  { key: 'class_name', header: '班级' },
];

const MOCK_STUDENTS: Student[] = [
  { id: '1', student_no: 'S001', name: '张三', gender: '男', age: 16, class_name: '高一(3)班' },
  { id: '2', student_no: 'S002', name: '李四', gender: '女', age: 16, class_name: '高一(3)班' },
  { id: '3', student_no: 'S003', name: '王五', gender: '男', age: 17, class_name: '高一(3)班' },
];

export function Students() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="学生管理"
        description="全校学生信息"
        actions={<Button>新增学生</Button>}
      />
      <DataTable
        columns={COLUMNS}
        data={MOCK_STUDENTS}
        searchable
        rowKey={(r) => r.id}
      />
    </div>
  );
}
