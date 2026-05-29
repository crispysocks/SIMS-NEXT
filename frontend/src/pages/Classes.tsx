import { useEffect } from 'react';
import { useClassStore } from '@/stores/classStore';
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

export function ClassesPage() {
  const {
    classes,
    total,
    page,
    pageSize,
    loading,
    error,
    modalOpen,
    editingClass,
    searchClassNo,
    searchClassName,
    fetchClasses,
    setPage,
    setSearchClassNo,
    setSearchClassName,
    openModal,
    closeModal,
    createClass,
    updateClass,
    deleteClass,
  } = useClassStore();

  useEffect(() => {
    fetchClasses();
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = {
      class_no: (form.elements.namedItem('class_no') as HTMLInputElement).value,
      class_name: (form.elements.namedItem('class_name') as HTMLInputElement).value,
      head_teacher_no: (form.elements.namedItem('head_teacher_no') as HTMLInputElement).value,
    };
    if (editingClass) {
      await updateClass(editingClass.id, data);
    } else {
      await createClass(data as any);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">班级管理</h1>
        <Button onClick={() => openModal()}>
          <Plus className="w-4 h-4 mr-2" />
          新增班级
        </Button>
      </div>

      <div className="flex gap-4">
        <Input
          placeholder="搜索班级编号..."
          value={searchClassNo}
          onChange={(e) => setSearchClassNo(e.target.value)}
          className="max-w-xs"
        />
        <Input
          placeholder="搜索班级名称..."
          value={searchClassName}
          onChange={(e) => setSearchClassName(e.target.value)}
          className="max-w-xs"
        />
      </div>

      {error && <div className="text-red-500">{error}</div>}

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>班级编号</TableHead>
            <TableHead>班级名称</TableHead>
            <TableHead>班主任工号</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {classes.map((cls) => (
            <TableRow key={cls.id}>
              <TableCell>{cls.class_no}</TableCell>
              <TableCell>{cls.class_name}</TableCell>
              <TableCell>{cls.head_teacher_no}</TableCell>
              <TableCell className="space-x-2">
                <Button variant="outline" size="sm" onClick={() => openModal(cls)}>
                  编辑
                </Button>
                <Button variant="destructive" size="sm" onClick={() => deleteClass(cls.id)}>
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
            <DialogTitle>{editingClass ? '编辑班级' : '新增班级'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="class_no">班级编号</Label>
              <Input id="class_no" name="class_no" defaultValue={editingClass?.class_no} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="class_name">班级名称</Label>
              <Input id="class_name" name="class_name" defaultValue={editingClass?.class_name} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="head_teacher_no">班主任工号</Label>
              <Input id="head_teacher_no" name="head_teacher_no" defaultValue={editingClass?.head_teacher_no} required />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={closeModal}>取消</Button>
              <Button type="submit">{editingClass ? '保存' : '创建'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}