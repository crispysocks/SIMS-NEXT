import { useEffect } from 'react';
import { useStudentStore } from '@/stores/studentStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Plus, Search } from 'lucide-react';

export function StudentsPage() {
  const {
    students,
    total,
    page,
    pageSize,
    loading,
    error,
    modalOpen,
    editingStudent,
    searchName,
    searchStudentNo,
    fetchStudents,
    setPage,
    setSearchName,
    setSearchStudentNo,
    openModal,
    closeModal,
    createStudent,
    updateStudent,
    deleteStudent,
  } = useStudentStore();

  useEffect(() => {
    fetchStudents();
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = {
      student_no: (form.elements.namedItem('student_no') as HTMLInputElement).value,
      name: (form.elements.namedItem('name') as HTMLInputElement).value,
      gender: (form.elements.namedItem('gender') as HTMLSelectElement).value,
      age: parseInt((form.elements.namedItem('age') as HTMLInputElement).value),
      enrollment_date: (form.elements.namedItem('enrollment_date') as HTMLInputElement).value,
    };
    if (editingStudent) {
      await updateStudent(editingStudent.student_no, data);
    } else {
      await createStudent(data as any);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">学生管理</h1>
        <Button onClick={() => openModal()}>
          <Plus className="w-4 h-4 mr-2" />
          新增学生
        </Button>
      </div>

      <div className="flex gap-4">
        <Input
          placeholder="搜索姓名..."
          value={searchName}
          onChange={(e) => setSearchName(e.target.value)}
          className="max-w-xs"
        />
        <Input
          placeholder="搜索学号..."
          value={searchStudentNo}
          onChange={(e) => setSearchStudentNo(e.target.value)}
          className="max-w-xs"
        />
      </div>

      {error && <div className="text-red-500">{error}</div>}

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>学号</TableHead>
            <TableHead>姓名</TableHead>
            <TableHead>性别</TableHead>
            <TableHead>年龄</TableHead>
            <TableHead>入学日期</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.map((student) => (
            <TableRow key={student.id}>
              <TableCell>{student.student_no}</TableCell>
              <TableCell>{student.name}</TableCell>
              <TableCell>{student.gender}</TableCell>
              <TableCell>{student.age}</TableCell>
              <TableCell>{student.enrollment_date}</TableCell>
              <TableCell className="space-x-2">
                <Button variant="outline" size="sm" onClick={() => openModal(student)}>
                  编辑
                </Button>
                <Button variant="destructive" size="sm" onClick={() => deleteStudent(student.student_no)}>
                  删除
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage(page - 1)}
          disabled={page === 1}
        >
          上一页
        </Button>
        <span className="text-sm">
          第 {page} 页，共 {Math.ceil(total / pageSize)} 页
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage(page + 1)}
          disabled={page >= Math.ceil(total / pageSize)}
        >
          下一页
        </Button>
      </div>

      <Dialog open={modalOpen} onOpenChange={(open) => !open && closeModal()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingStudent ? '编辑学生' : '新增学生'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="student_no">学号</Label>
              <Input id="student_no" name="student_no" defaultValue={editingStudent?.student_no} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">姓名</Label>
              <Input id="name" name="name" defaultValue={editingStudent?.name} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="gender">性别</Label>
              <select id="gender" name="gender" defaultValue={editingStudent?.gender} className="w-full border rounded-md px-3 py-2" required>
                <option value="">请选择</option>
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="age">年龄</Label>
              <Input id="age" name="age" type="number" defaultValue={editingStudent?.age} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="enrollment_date">入学日期</Label>
              <Input id="enrollment_date" name="enrollment_date" type="date" defaultValue={editingStudent?.enrollment_date?.split('T')[0]} required />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={closeModal}>取消</Button>
              <Button type="submit">{editingStudent ? '保存' : '创建'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}