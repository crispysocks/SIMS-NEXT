import { useEffect } from 'react';
import { useScoreStore } from '@/stores/scoreStore';
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

export function ScoresPage() {
  const {
    scores,
    total,
    page,
    pageSize,
    loading,
    error,
    modalOpen,
    editingScore,
    searchStudentNo,
    searchExamName,
    searchStudentName,
    fetchScores,
    setPage,
    setSearchStudentNo,
    setSearchExamName,
    setSearchStudentName,
    openModal,
    closeModal,
    createScore,
    updateScore,
    deleteScore,
  } = useScoreStore();

  useEffect(() => {
    fetchScores();
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = {
      student_no: (form.elements.namedItem('student_no') as HTMLInputElement).value,
      student_name: (form.elements.namedItem('student_name') as HTMLInputElement).value,
      exam_name: (form.elements.namedItem('exam_name') as HTMLInputElement).value,
      score: parseFloat((form.elements.namedItem('score') as HTMLInputElement).value),
    };
    if (editingScore) {
      await updateScore(editingScore.id, data);
    } else {
      await createScore(data as any);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">成绩管理</h1>
        <Button onClick={() => openModal()}>
          <Plus className="w-4 h-4 mr-2" />
          新增成绩
        </Button>
      </div>

      <div className="flex gap-4">
        <Input
          placeholder="搜索学号..."
          value={searchStudentNo}
          onChange={(e) => setSearchStudentNo(e.target.value)}
          className="max-w-xs"
        />
        <Input
          placeholder="搜索学生姓名..."
          value={searchStudentName}
          onChange={(e) => setSearchStudentName(e.target.value)}
          className="max-w-xs"
        />
        <Input
          placeholder="搜索考试名称..."
          value={searchExamName}
          onChange={(e) => setSearchExamName(e.target.value)}
          className="max-w-xs"
        />
      </div>

      {error && <div className="text-red-500">{error}</div>}

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>学号</TableHead>
            <TableHead>学生姓名</TableHead>
            <TableHead>考试名称</TableHead>
            <TableHead>分数</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scores.map((score) => (
            <TableRow key={score.id}>
              <TableCell>{score.student_no}</TableCell>
              <TableCell>{score.student_name}</TableCell>
              <TableCell>{score.exam_name}</TableCell>
              <TableCell>{score.score.toFixed(2)}</TableCell>
              <TableCell className="space-x-2">
                <Button variant="outline" size="sm" onClick={() => openModal(score)}>
                  编辑
                </Button>
                <Button variant="destructive" size="sm" onClick={() => deleteScore(score.id)}>
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
            <DialogTitle>{editingScore ? '编辑成绩' : '新增成绩'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="student_no">学号</Label>
              <Input id="student_no" name="student_no" defaultValue={editingScore?.student_no} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="student_name">学生姓名</Label>
              <Input id="student_name" name="student_name" defaultValue={editingScore?.student_name} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="exam_name">考试名称</Label>
              <Input id="exam_name" name="exam_name" defaultValue={editingScore?.exam_name} placeholder="如：月考1, 期中考试, 期末考试" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="score">分数</Label>
              <Input id="score" name="score" type="number" step="0.01" defaultValue={editingScore?.score} required />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={closeModal}>取消</Button>
              <Button type="submit">{editingScore ? '保存' : '创建'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}