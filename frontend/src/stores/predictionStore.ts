import { create } from 'zustand';
import { api } from '@/lib/api';

export interface Student {
  id: number;
  student_no: string;
  name: string;
  gender: string;
  age: number;
  enrollment_date: string;
}

export interface SchoolPrediction {
  school_name: string;
  predicted_score: number;
  admission_probability: number;
  admission_type: string;
  score_diff: number;
}

export interface PredictionResult {
  student_id: number;
  current_score: number;
  current_ranking: number;
  predicted_ranking: number;
  ranking_trend: string;
  predictions: {
    冲刺: SchoolPrediction[];
    稳定: SchoolPrediction[];
    保底: SchoolPrediction[];
  };
}

export interface RiskWarning {
  risk_level: string;
  risk_tags: string[];
}

export interface SimulationResult {
  subject: string;
  score_increase: number;
  key_high_school_probability_change: string;
  ranking_improvement: string;
}

interface ChatMessage {
  role: string;
  content: string;
}

interface PredictionState {
  students: Student[];
  selectedStudent: Student | null;
  currentScore: number;
  prediction: PredictionResult | null;
  risk: RiskWarning | null;
  simulations: SimulationResult[];
  chatOpen: boolean;
  chatMessages: ChatMessage[];
  loading: boolean;
  error: string | null;
  simulationScore: string;
  simulationResult: PredictionResult | null;
  simulationLoading: boolean;
  fetchStudents: () => Promise<void>;
  selectStudent: (student: Student) => void;
  fetchPredictionData: (studentId: number, currentScore?: number) => Promise<void>;
  setChatOpen: (open: boolean) => void;
  sendChatMessage: (message: string) => void;
  clearChat: () => void;
  setSimulationScore: (score: string) => void;
  runSimulation: (studentId: number) => Promise<void>;
  clearSimulation: () => void;
}

export const usePredictionStore = create<PredictionState>()((set, get) => ({
  students: [],
  selectedStudent: null,
  currentScore: 0,
  prediction: null,
  risk: null,
  simulations: [],
  chatOpen: false,
  chatMessages: [],
  loading: false,
  error: null,
  simulationScore: '',
  simulationResult: null,
  simulationLoading: false,

  fetchStudents: async () => {
    set({ loading: true, error: null });
    try {
      const data = await api.get<{ items: Student[]; total: number }>(
        '/students?page=1&page_size=100'
      );
      set({ students: data.items, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取学生列表失败', loading: false });
    }
  },

  selectStudent: (student) => {
    set({
      selectedStudent: student,
      prediction: null,
      risk: null,
      simulations: [],
      chatMessages: [],
      error: null,
      simulationScore: '',
      simulationResult: null,
    });
  },

  fetchPredictionData: async (studentId: number, currentScore?: number) => {
    set({ loading: true, error: null });
    try {
      const url = currentScore !== undefined
        ? `/predict/${studentId}?current_score=${currentScore}`
        : `/predict/${studentId}`;
      const [prediction, risk] = await Promise.all([
        api.get<PredictionResult>(url),
        api.get<RiskWarning>(`/predict/${studentId}/risk`),
      ]);
      set({ prediction, risk, currentScore: prediction.current_score, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取预测数据失败', loading: false });
    }
  },

  setChatOpen: (open) => set({ chatOpen: open }),

  sendChatMessage: (message) => {
    const { selectedStudent, chatMessages } = get();
    if (!selectedStudent) return;

    // Add user message
    const newMessages = [...chatMessages, { role: 'user', content: message }];
    set({ chatMessages: newMessages, chatOpen: true });

    const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
    const controller = new AbortController();

    let assistantContent = '';
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    fetch(`${API_BASE}/advice/${selectedStudent.id}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
      signal: controller.signal,
    }).then(response => {
      clearTimeout(timeoutId);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      const processChunk = ({ done, value }: { done: boolean; value?: Uint8Array }) => {
        if (done) {
          // Process remaining buffer
          if (buffer) {
            try {
              const data = buffer.trim();
              if (data.startsWith('data: ')) {
                const jsonStr = data.slice(6);
                const parsed = JSON.parse(jsonStr);
                if (parsed.content) {
                  assistantContent += parsed.content;
                }
              }
            } catch {}
          }
          // Add final assistant message
          if (assistantContent) {
            set((state) => ({
              chatMessages: [...state.chatMessages, { role: 'assistant', content: assistantContent }]
            }));
          }
          return;
        }

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                assistantContent += parsed.content;
                // Update messages with current accumulated content
                set((state) => {
                  const msgs = [...state.chatMessages];
                  // Find or create assistant message
                  const lastMsg = msgs[msgs.length - 1];
                  if (lastMsg && lastMsg.role === 'assistant') {
                    msgs[msgs.length - 1] = { role: 'assistant', content: assistantContent };
                  } else {
                    msgs.push({ role: 'assistant', content: assistantContent });
                  }
                  return { chatMessages: msgs };
                });
              }
              if (parsed.done) {
                reader.cancel();
                return;
              }
            } catch (e) {
              console.warn('SSE parse error:', e);
            }
          }
        }

        reader.read().then(processChunk);
      };

      reader.read().then(processChunk);
    }).catch(err => {
      clearTimeout(timeoutId);
      console.error('Chat fetch error:', err);

      let errorMessage = '连接失败，请稍后重试';
      if (err.name === 'AbortError') {
        errorMessage = '请求超时，请检查网络连接';
      } else if (err.message.includes('HTTP')) {
        errorMessage = `服务器错误: ${err.message}`;
      }

      set((state) => ({
        chatMessages: [...state.chatMessages, { role: 'assistant', content: errorMessage }]
      }));
    });
  },

  clearChat: () => set({ chatMessages: [] }),

  setSimulationScore: (score) => set({ simulationScore: score }),

  runSimulation: async (studentId: number) => {
    const { simulationScore } = get();
    if (!simulationScore || isNaN(parseInt(simulationScore))) {
      set({ error: '请输入有效的分数' });
      return;
    }

    set({ simulationLoading: true, error: null });
    try {
      const url = `/predict/${studentId}?current_score=${parseInt(simulationScore)}`;
      const result = await api.get<PredictionResult>(url);
      set({ simulationResult: result, simulationLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '模拟失败', simulationLoading: false });
    }
  },

  clearSimulation: () => set({ simulationScore: '', simulationResult: null }),
}));