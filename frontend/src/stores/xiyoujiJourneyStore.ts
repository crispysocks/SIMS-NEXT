import { create } from 'zustand';
import { api } from '@/lib/api';

// ── Types ────────────────────────────────────

export interface KnowledgeCard {
  title: string;
  content: string;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  unlocked: boolean;
}

export interface ChoiceItem {
  text: string;
  karma: number;
  success: boolean;
}

export interface JourneyResponse {
  think: string | null;
  reply: string;
  scene_description: string;
  stage: string;
  choices: ChoiceItem[];
  progress: number;
  karma: number;
  chapter: number;
  level_id: number;
  chapter_name: string;
  monster_name: string;
  monster_description: string;
  knowledge_card: KnowledgeCard | null;
  achievements: Achievement[];
}

export interface JourneyStatus {
  session_id: string;
  user_role: string;
  current_stage: string;
  progress: number;
  karma: number;
  companions: string[];
  chapter: number;
  level_id: number;
  knowledge_cards: KnowledgeCard[];
  achievements: Achievement[];
  cleared_chapters: number[];
}

// ── Store ────────────────────────────────────

interface JourneyState {
  sessionId: string | null;
  gameActive: boolean;
  loading: boolean;
  error: string | null;

  // Current game state
  currentStage: string;
  progress: number;
  karma: number;
  chapter: number;
  levelId: number;
  chapterName: string;
  sceneDescription: string;
  monsterName: string;
  monsterDescription: string;
  choices: ChoiceItem[];
  knowledgeCard: KnowledgeCard | null;
  achievements: Achievement[];
  knowledgeCards: KnowledgeCard[];
  clearedChapters: number[];

  // Messages
  messages: { role: 'assistant' | 'user'; content: string }[];

  startGame: (sessionId: string) => Promise<void>;
  makeChoice: (choice: string) => Promise<void>;
  resetGame: () => void;
  fetchStatus: (sessionId: string) => Promise<void>;
}

export const useXiyoujiJourneyStore = create<JourneyState>()((set, get) => ({
  sessionId: null,
  gameActive: false,
  loading: false,
  error: null,
  currentStage: '',
  progress: 0,
  karma: 0,
  chapter: 0,
  levelId: 0,
  chapterName: '',
  sceneDescription: '',
  monsterName: '',
  monsterDescription: '',
  choices: [],
  knowledgeCard: null,
  achievements: [],
  knowledgeCards: [],
  clearedChapters: [],
  messages: [],

  startGame: async (sessionId) => {
    set({ loading: true, error: null, sessionId });
    try {
      const result = await api.post<JourneyResponse>('/xiyouji/journey/start', {
        session_id: sessionId,
      });
      set({
        loading: false,
        gameActive: true,
        currentStage: result.stage,
        progress: result.progress,
        karma: result.karma,
        chapter: result.chapter,
        levelId: result.level_id,
        chapterName: result.chapter_name,
        sceneDescription: result.scene_description,
        monsterName: result.monster_name,
        monsterDescription: result.monster_description,
        choices: result.choices,
        achievements: result.achievements,
        messages: [{ role: 'assistant', content: result.reply }],
      });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  makeChoice: async (choice) => {
    const { sessionId } = get();
    if (!sessionId) return;

    set({ loading: true, error: null });
    set((s) => ({
      messages: [...s.messages, { role: 'user', content: choice }],
    }));

    try {
      const result = await api.post<JourneyResponse>('/xiyouji/journey/choice', {
        session_id: sessionId,
        choice,
      });

      const newCards = result.knowledge_card
        ? [...get().knowledgeCards, result.knowledge_card]
        : get().knowledgeCards;

      set((s) => ({
        loading: false,
        currentStage: result.stage,
        progress: result.progress,
        karma: result.karma,
        chapter: result.chapter,
        levelId: result.level_id,
        chapterName: result.chapter_name,
        sceneDescription: result.scene_description,
        monsterName: result.monster_name,
        monsterDescription: result.monster_description,
        choices: result.choices,
        knowledgeCard: result.knowledge_card,
        knowledgeCards: newCards,
        achievements: result.achievements,
        clearedChapters: result.chapter > (s.chapter || 0) ? [...s.clearedChapters, s.chapter] : s.clearedChapters,
        messages: [...s.messages, { role: 'assistant', content: result.reply }],
      }));
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  resetGame: () => {
    set({
      sessionId: null,
      gameActive: false,
      loading: false,
      error: null,
      currentStage: '',
      progress: 0,
      karma: 0,
      chapter: 0,
      levelId: 0,
      chapterName: '',
      sceneDescription: '',
      monsterName: '',
      monsterDescription: '',
      choices: [],
      knowledgeCard: null,
      achievements: [],
      knowledgeCards: [],
      clearedChapters: [],
      messages: [],
    });
  },

  fetchStatus: async (sessionId) => {
    try {
      const status = await api.get<JourneyStatus>(`/xiyouji/journey/status?session_id=${sessionId}`);
      if (status.chapter > 0) {
        set({
          gameActive: true,
          sessionId,
          karma: status.karma,
          chapter: status.chapter,
          levelId: status.level_id,
          achievements: status.achievements,
          knowledgeCards: status.knowledge_cards,
          clearedChapters: status.cleared_chapters,
        });
      }
    } catch {
      // not in game
    }
  },
}));