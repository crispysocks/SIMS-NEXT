import { create } from 'zustand';

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

export interface GameEventData {
  reply?: string;
  scene_description?: string;
  stage?: string;
  choices?: ChoiceItem[];
  progress?: number;
  karma?: number;
  chapter?: number;
  level_id?: number;
  chapter_name?: string;
  monster_name?: string;
  monster_description?: string;
  knowledge_card?: KnowledgeCard | null;
  achievements?: Achievement[];
}

interface JourneyState {
  gameActive: boolean;
  chapter: number;
  chapterName: string;
  progress: number;
  karma: number;
  stage: string;
  sceneDescription: string;
  monsterName: string;
  monsterDescription: string;
  choices: ChoiceItem[];
  knowledgeCards: KnowledgeCard[];
  achievements: Achievement[];

  applyGameEvent: (data: GameEventData) => void;
  reset: () => void;
}

export const useJourneyStore = create<JourneyState>()((set, get) => ({
  gameActive: false,
  chapter: 0,
  chapterName: '',
  progress: 0,
  karma: 0,
  stage: '',
  sceneDescription: '',
  monsterName: '',
  monsterDescription: '',
  choices: [],
  knowledgeCards: [],
  achievements: [],

  applyGameEvent: (data) => {
    const state = get();
    set({
      gameActive: true,
      chapter: data.chapter ?? state.chapter,
      chapterName: data.chapter_name ?? state.chapterName,
      progress: data.progress ?? state.progress,
      karma: data.karma ?? state.karma,
      stage: data.stage ?? state.stage,
      sceneDescription: data.scene_description ?? state.sceneDescription,
      monsterName: data.monster_name ?? state.monsterName,
      monsterDescription: data.monster_description ?? state.monsterDescription,
      choices: data.choices ?? state.choices,
      knowledgeCards: data.knowledge_card
        ? [...state.knowledgeCards, data.knowledge_card]
        : state.knowledgeCards,
      achievements: data.achievements ?? state.achievements,
    });
  },

  reset: () => {
    set({
      gameActive: false,
      chapter: 0,
      chapterName: '',
      progress: 0,
      karma: 0,
      stage: '',
      sceneDescription: '',
      monsterName: '',
      monsterDescription: '',
      choices: [],
      knowledgeCards: [],
      achievements: [],
    });
  },
}));
