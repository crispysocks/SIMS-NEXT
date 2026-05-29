import { useEffect } from 'react';
import { useTeacherStore } from '@/stores/teacherStore';
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

export function TeachersPage() {
  const {
    teachers,
    total,
    page,
    pageSize,
    loading,
    error,
    modalOpen,
    editingTeacher,
    searchName,
    searchTeacherNo,
    fetchTeachers,
    setPage,
    setSearchName,
    setSearchTeacherNo,
    openModal,
    closeModal,
    createTeacher,
    updateTeacher,
    deleteTeacher,
  } = useTeacherStore();

  useEffect(() => {
    fetchTeachers();
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = {
      teacher_no: (form.elements.namedItem('teacher_no') as HTMLInputElement).value,
      name: (form.elements.namedItem('name') as HTMLInputElement).value,
      gender: (form.elements.namedItem('gender') as HTMLSelectElement).value,
      entry_date: (form.elements.namedItem('entry_date') as HTMLInputElement).value,
    };
    if (editingTeacher) {
      await updateTeacher(editingTeacher.teacher_no, data);
    } else {
      await createTeacher(data as any);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">教师管理</h1>
        <Button onClick={() => openModal()}>
          <Plus className="w-4 h-4 mr-2" />
          新增教师
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
          placeholder="搜索工号..."
          value={searchTeacherNo}
          onChange={(e) => setSearchTeacherNo(e.target.value)}
          className="max-w-xs"
        />
      </div>

      {error && <div className="text-red-500">{error}</div>}

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>工号</TableHead>
            <TableHead>姓名</TableHead>
            <TableHead>性别</TableHead>
            <TableHead>入职日期</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {teachers.map((teacher) => (
            <TableRow key={teacher.id}>
              <TableCell>{teacher.teacher_no}</TableCell>
              <TableCell>{teacher.name}</TableCell>
              <TableCell>{teacher.gender}</TableCell>
              <TableCell>{teacher.entry_date}</TableCell>
              <TableCell className="space-x-2">
                <Button variant="outline" size="sm" onClick={() => openModal(teacher)}>
                  编辑
                </Button>
                <Button variant="destructive" size="sm" onClick={() => deleteTeacher(teacher.teacher_no)}>
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
            <DialogTitle>{editingTeacher ? '编辑教师' : '新增教师'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="teacher_no">工号</Label>
              <Input id="teacher_no" name="teacher_no" defaultValue={editingTeacher?.teacher_no} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">姓名</Label>
              <Input id="name" name="name" defaultValue={editingTeacher?.name} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="gender">性别</Label>
              <select id="gender" name="gender" defaultValue={editingTeacher?.gender} className="w-full border rounded-md px-3 py-2" required>
                <option value="">请选择</option>
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="entry_date">入职日期</Label>
              <Input id="entry_date" name="entry_date" type="date" defaultValue={editingTeacher?.entry_date?.split('T')[0]} required />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={closeModal}>取消</Button>
              <Button type="submit">{editingTeacher ? '保存' : '创建'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}