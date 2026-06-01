export interface Question {
  id: string;
  text: string;
  options: Array<{ id: string; label: string }>;
}

export interface SubmitResult {
  correct: boolean;
  explanation: string;
}

export const tutorApi = {
  async getNextQuestion(): Promise<Question> {
    // TODO: real endpoint
    return {
      id: 'q1',
      text: '已知二次函数 y = x² + 2x + 1，求其顶点坐标。',
      options: [
        { id: 'A', label: '(-1, 0)' },
        { id: 'B', label: '(1, 0)' },
        { id: 'C', label: '(-1, 4)' },
        { id: 'D', label: '(0, 1)' },
      ],
    };
  },
  async submitAnswer(_: { questionId: string; optionId: string }): Promise<SubmitResult> {
    // TODO: real endpoint
    return {
      correct: true,
      explanation: '二次函数 y = (x+1)² 的顶点是 (-1, 0)。',
    };
  },
};
