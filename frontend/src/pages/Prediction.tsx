import { useEffect, useRef, useState } from 'react';
import { usePredictionStore } from '@/stores/predictionStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { MessageSquare, TrendingUp, TrendingDown, AlertTriangle, Target, Calculator } from 'lucide-react';

export function PredictionPage() {
  const {
    students,
    selectedStudent,
    currentScore,
    prediction,
    risk,
    chatOpen,
    chatMessages,
    loading,
    error,
    fetchStudents,
    fetchPredictionData,
    selectStudent,
    setChatOpen,
    sendChatMessage,
    clearChat,
    simulationScore,
    simulationResult,
    simulationLoading,
    setSimulationScore,
    runSimulation,
    clearSimulation,
  } = usePredictionStore();

  const [chatInput, setChatInput] = useState('');
  const [selectedSchool, setSelectedSchool] = useState<string>('');
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  useEffect(() => {
    const el = chatContainerRef.current;
    if (!el) return;
    if (isAtBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [chatMessages]);

  const handleChatScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    isAtBottomRef.current = distanceFromBottom < 50;
  };

  const handleStudentSelect = (studentId: string) => {
    const student = students.find((s) => s.id === parseInt(studentId));
    if (student) {
      selectStudent(student);
      fetchPredictionData(student.id);
    }
  };

  const handleSimulate = () => {
    if (selectedStudent && simulationScore) {
      runSimulation(selectedStudent.id);
    }
  };

  const handleSendMessage = () => {
    if (chatInput.trim()) {
      sendChatMessage(chatInput);
      setChatInput('');
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case '高':
      case '高风险':
        return 'text-red-600 bg-red-50 border-red-200';
      case '中':
      case '中风险':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case '低':
      case '低风险':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getTrendIcon = (trend: string) => {
    if (trend.includes('上升') || trend.includes('提高')) {
      return <TrendingUp className="w-6 h-6 text-green-600" />;
    } else if (trend.includes('下降') || trend.includes('降低')) {
      return <TrendingDown className="w-6 h-6 text-red-600" />;
    }
    return null;
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case '冲刺':
        return 'bg-red-100 text-red-700';
      case '稳定':
        return 'bg-yellow-100 text-yellow-700';
      case '保底':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getCategoryBorderColor = (category: string) => {
    switch (category) {
      case '冲刺':
        return 'border-red-300';
      case '稳定':
        return 'border-yellow-300';
      case '保底':
        return 'border-green-300';
      default:
        return 'border-gray-300';
    }
  };

  // Get all schools from current prediction for school selector
  const getAllSchools = () => {
    if (!prediction) return [];
    const schools: Array<{ name: string; category: string; score: number; probability: number }> = [];
    const categories = ['冲刺', '稳定', '保底'] as const;
    categories.forEach(cat => {
      if (prediction.predictions[cat]) {
        prediction.predictions[cat].forEach(school => {
          schools.push({
            name: school.school_name,
            category: cat,
            score: school.predicted_score,
            probability: school.admission_probability,
          });
        });
      }
    });
    return schools;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">升学预测AI</h1>
        <p className="text-gray-500 text-sm mt-1">基于数据分析的智能升学预测与建议</p>
      </div>

      {/* Student Selector */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="w-64">
              <label className="text-sm font-medium mb-2 block">选择学生</label>
              <Select onValueChange={handleStudentSelect}>
                <SelectTrigger>
                  <SelectValue placeholder="请选择学生..." />
                </SelectTrigger>
                <SelectContent>
                  {students.map((student) => (
                    <SelectItem key={student.id} value={student.id.toString()}>
                      {student.name} ({student.student_no})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedStudent && (
              <div className="flex items-center gap-6 text-sm">
                <div>
                  <span className="text-gray-500">学号:</span>
                  <span className="ml-2 font-medium">{selectedStudent.student_no}</span>
                </div>
                <div>
                  <span className="text-gray-500">姓名:</span>
                  <span className="ml-2 font-medium">{selectedStudent.name}</span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {selectedStudent && prediction && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-blue-600 font-medium">当前分数</p>
                  <p className="text-3xl font-bold text-blue-700 mt-2">{currentScore}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-purple-50 border-purple-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-center gap-3">
                  <div className="text-center">
                    <p className="text-sm text-purple-600 font-medium">排名趋势</p>
                    <div className="flex items-center justify-center mt-2">
                      {getTrendIcon(prediction.ranking_trend)}
                      <p className="text-2xl font-bold text-purple-700 ml-2">
                        {prediction.current_ranking} → {prediction.predicted_ranking}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className={getRiskColor(risk?.risk_level || '未知')}>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm font-medium">风险预警</p>
                  <div className="flex items-center justify-center mt-2">
                    <AlertTriangle className="w-6 h-6 mr-2" />
                    <p className="text-2xl font-bold">{risk?.risk_level || '未知'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Risk Tags */}
          {risk && risk.risk_tags && risk.risk_tags.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">风险因素</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {risk.risk_tags.map((tag, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* School Recommendations */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 冲刺学校 */}
            <Card className="border-red-200 bg-red-50/50">
              <CardHeader className="bg-red-100/50 pb-3">
                <CardTitle className="text-red-700 flex items-center">
                  <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                  冲刺学校
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {prediction.predictions.冲刺 && prediction.predictions.冲刺.length > 0 ? (
                  <ul className="space-y-3">
                    {prediction.predictions.冲刺.map((school, index) => (
                      <li key={index} className="flex items-start">
                        <div className="flex-1">
                          <p className="font-medium">{school.school_name}</p>
                          <p className="text-sm text-gray-500 mt-1">
                            预测分数: {school.predicted_score} | 差距: {school.score_diff}分
                          </p>
                        </div>
                        <span className="ml-2 px-2 py-1 bg-red-100 text-red-700 rounded text-sm font-medium">
                          {school.admission_probability}%
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-center py-4">暂无数据</p>
                )}
              </CardContent>
            </Card>

            {/* 稳定学校 */}
            <Card className="border-yellow-200 bg-yellow-50/50">
              <CardHeader className="bg-yellow-100/50 pb-3">
                <CardTitle className="text-yellow-700 flex items-center">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                  稳定学校
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {prediction.predictions.稳定 && prediction.predictions.稳定.length > 0 ? (
                  <ul className="space-y-3">
                    {prediction.predictions.稳定.map((school, index) => (
                      <li key={index} className="flex items-start">
                        <div className="flex-1">
                          <p className="font-medium">{school.school_name}</p>
                          <p className="text-sm text-gray-500 mt-1">
                            预测分数: {school.predicted_score}
                          </p>
                        </div>
                        <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-sm font-medium">
                          {school.admission_probability}%
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-center py-4">暂无数据</p>
                )}
              </CardContent>
            </Card>

            {/* 保底学校 */}
            <Card className="border-green-200 bg-green-50/50">
              <CardHeader className="bg-green-100/50 pb-3">
                <CardTitle className="text-green-700 flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  保底学校
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {prediction.predictions.保底 && prediction.predictions.保底.length > 0 ? (
                  <ul className="space-y-3">
                    {prediction.predictions.保底.map((school, index) => (
                      <li key={index} className="flex items-start">
                        <div className="flex-1">
                          <p className="font-medium">{school.school_name}</p>
                          <p className="text-sm text-gray-500 mt-1">
                            预测分数: {school.predicted_score}
                          </p>
                        </div>
                        <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 rounded text-sm font-medium">
                          {school.admission_probability}%
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-center py-4">暂无数据</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Simulation Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                加分模拟
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="byScore" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="byScore">按分数模拟</TabsTrigger>
                  <TabsTrigger value="bySchool">按学校选择</TabsTrigger>
                </TabsList>

                {/* Tab 1: 按分数模拟 */}
                <TabsContent value="byScore" className="space-y-4 mt-4">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        placeholder="输入目标分数"
                        value={simulationScore}
                        onChange={(e) => setSimulationScore(e.target.value)}
                        className="w-40"
                        onKeyDown={(e) => e.key === 'Enter' && handleSimulate()}
                      />
                      <Button onClick={handleSimulate} disabled={simulationLoading || !simulationScore}>
                        {simulationLoading ? '计算中...' : '模拟'}
                      </Button>
                    </div>
                    <Button variant="ghost" onClick={clearSimulation}>
                      清空
                    </Button>
                  </div>

                  {simulationResult && (
                    <div className="mt-4 p-4 bg-slate-50 rounded-lg">
                      <div className="flex items-center gap-2 mb-4">
                        <Target className="w-5 h-5 text-blue-600" />
                        <span className="font-medium">
                          目标分数: {simulationResult.current_score} 分
                        </span>
                        <span className={`px-2 py-1 rounded text-sm ${getCategoryColor(getCategoryForScore(simulationResult.current_score))}`}>
                          {getCategoryForScore(simulationResult.current_score)}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {renderSimulationResults(simulationResult.predictions)}
                      </div>

                      <div className="mt-4 text-sm text-gray-500">
                        当前分数 {currentScore} → 目标分数 {simulationResult.current_score}
                        (差 {simulationResult.current_score - currentScore > 0 ? '+' : ''}{simulationResult.current_score - currentScore} 分)
                      </div>
                    </div>
                  )}
                </TabsContent>

                {/* Tab 2: 按学校选择 */}
                <TabsContent value="bySchool" className="space-y-4 mt-4">
                  <div className="flex items-center gap-4">
                    <Select onValueChange={setSelectedSchool} value={selectedSchool}>
                      <SelectTrigger className="w-64">
                        <SelectValue placeholder="选择学校查看详情" />
                      </SelectTrigger>
                      <SelectContent>
                        {getAllSchools().map((school) => (
                          <SelectItem key={school.name} value={school.name}>
                            {school.name} ({school.category})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {selectedSchool && (
                      <Button variant="ghost" onClick={() => setSelectedSchool('')}>
                        清空
                      </Button>
                    )}
                  </div>

                  {selectedSchool && (
                    <SchoolDetail
                      school={getAllSchools().find(s => s.name === selectedSchool)!}
                      currentScore={currentScore}
                    />
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </>
      )}

      {/* AI Chat Button */}
      {selectedStudent && (
        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={() => setChatOpen(true)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            <MessageSquare className="w-5 h-5 mr-2" />
            咨询AI
          </Button>
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* AI Chat Dialog */}
      <Dialog open={chatOpen} onOpenChange={setChatOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              AI升学顾问
              {selectedStudent && (
                <span className="text-sm font-normal text-gray-500">
                  - {selectedStudent.name}
                </span>
              )}
            </DialogTitle>
          </DialogHeader>
          <div
            ref={chatContainerRef}
            onScroll={handleChatScroll}
            className="flex-1 min-h-0 overflow-y-auto space-y-4"
          >
            {chatMessages.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>您好！我是您的AI升学顾问。</p>
                <p className="text-sm mt-2">可以问我关于升学预测、学校选择、学习规划等问题。</p>
              </div>
            ) : (
              chatMessages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))
            )}
          </div>
          <div className="flex gap-2 mt-4 pt-4 border-t">
            <Input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
              placeholder="输入您的问题..."
              disabled={!selectedStudent}
            />
            <Button onClick={handleSendMessage} disabled={!chatInput.trim() || !selectedStudent}>
              发送
            </Button>
          </div>
          {chatMessages.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearChat}
              className="mt-2 text-gray-500"
            >
              清空对话
            </Button>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Helper function to determine category based on score
function getCategoryForScore(score: number): string {
  if (!simulationResult?.predictions) return '待定';

  const { predictions } = simulationResult;
  const hasChase = predictions.冲刺 && predictions.冲刺.length > 0;
  const hasStable = predictions.稳定 && predictions.稳定.length > 0;
  const hasBackup = predictions.保底 && predictions.保底.length > 0;

  if (hasChase) return '冲刺';
  if (hasStable) return '稳定';
  if (hasBackup) return '保底';
  return '待定';
}

// Helper component to render simulation results
function renderSimulationResults(predictions: {
  冲刺: Array<{ school_name: string; predicted_score: number; admission_probability: number; score_diff: number }>;
  稳定: Array<{ school_name: string; predicted_score: number; admission_probability: number; score_diff: number }>;
  保底: Array<{ school_name: string; predicted_score: number; admission_probability: number; score_diff: number }>;
}) {
  const categories = [
    { key: '冲刺', label: '冲刺学校', color: 'red' },
    { key: '稳定', label: '稳定学校', color: 'yellow' },
    { key: '保底', label: '保底学校', color: 'green' },
  ] as const;

  return categories.map(({ key, label, color }) => (
    <div key={key} className={`border border-${color}-200 rounded-lg p-3`}>
      <h4 className={`font-medium text-${color}-700 mb-2`}>{label}</h4>
      {predictions[key] && predictions[key].length > 0 ? (
        <ul className="space-y-1">
          {predictions[key].map((school, idx) => (
            <li key={idx} className="text-sm">
              <span className="font-medium">{school.school_name}</span>
              <span className="ml-2 text-gray-500">概率 {school.admission_probability}%</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-400">无</p>
      )}
    </div>
  ));
}

// Helper component to show school detail
function SchoolDetail({
  school,
  currentScore,
}: {
  school: { name: string; category: string; score: number; probability: number };
  currentScore: number;
}) {
  const scoreDiff = currentScore - school.score;
  const scoreDiffStr = scoreDiff > 0 ? `+${scoreDiff}` : `${scoreDiff}`;

  return (
    <div className="mt-4 p-4 bg-slate-50 rounded-lg">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-medium text-lg">{school.name}</h3>
          <span className={`inline-block px-2 py-1 rounded text-sm mt-1 ${
            school.category === '冲刺' ? 'bg-red-100 text-red-700' :
            school.category === '稳定' ? 'bg-yellow-100 text-yellow-700' :
            'bg-green-100 text-green-700'
          }`}>
            {school.category}
          </span>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-blue-600">{school.probability}%</p>
          <p className="text-sm text-gray-500">录取概率</p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="bg-white p-3 rounded border">
          <p className="text-sm text-gray-500">学校录取分数</p>
          <p className="text-lg font-medium">{school.score} 分</p>
        </div>
        <div className="bg-white p-3 rounded border">
          <p className="text-sm text-gray-500">你的分数</p>
          <p className="text-lg font-medium">{currentScore} 分</p>
        </div>
        <div className="bg-white p-3 rounded border">
          <p className="text-sm text-gray-500">分差</p>
          <p className={`text-lg font-medium ${scoreDiff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {scoreDiffStr} 分
          </p>
        </div>
        <div className="bg-white p-3 rounded border">
          <p className="text-sm text-gray-500">概率</p>
          <p className="text-lg font-medium">{school.probability}%</p>
        </div>
      </div>
    </div>
  );
}