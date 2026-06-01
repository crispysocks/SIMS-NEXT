import { api } from '@/lib/api';

// 1:1 mirror of backend Pydantic schemas in `app/predict/schemas/*.py`.
// Field names kept in sync with the backend.

// -- /predict/* endpoints -----------------------------------------------------

export interface PredictionItem {
  school_name: string;
  predicted_score: number;
  admission_probability: number;
  admission_type: string;
  score_diff: number;
}

// StudentPrediction.predictions is a dict keyed by category (冲刺/稳定/保底),
// each holding a list of `PredictionItem` per school in that tier.
export interface StudentPrediction {
  student_id: number;
  current_score: number;
  current_ranking: number;
  predicted_ranking: number;
  ranking_trend: string;
  predictions: {
    冲刺?: PredictionItem[];
    稳定?: PredictionItem[];
    保底?: PredictionItem[];
    [key: string]: PredictionItem[] | undefined;
  };
}

export interface StudentScore {
  total_score: number;
  count: number;
}

export interface StudentPortraitDetail {
  student_id: number;
  updated_at: string;
  learning_type: string | null;
  science_ability: string | null;
  english_ability: string | null;
  improvement_potential: string | null;
}

// RiskWarning only carries a level + tags. Per-subject risk detail is not
// returned by the backend; the UI can derive risks from risk_tags.
export interface RiskWarning {
  risk_level: string;
  risk_tags: string[];
}

export interface WhatIfResult {
  subject: string;
  score_increase: number;
  key_high_school_probability_change: string;
  ranking_improvement: string;
}

// -- /admission-line/* endpoints ---------------------------------------------

export interface ScoreLinePrediction {
  school_name: string;
  last_year_score: number;
  predicted_score: number;
  fluctuation: string;
}

// -- /advice/* endpoints -----------------------------------------------------

export interface SubjectAdvice {
  subject: string;
  advice: string;
  expected_improvement: string;
}

export interface AIAdvice {
  current_tier: string;
  target_tier: string;
  suggestions: SubjectAdvice[];
  overall_expected_improvement: string;
}

// -- API client ---------------------------------------------------------------

export const predictionApi = {
  get: (studentId: number) => api.get<StudentPrediction>(`/predict/${studentId}`),

  getScore: (studentId: number) => api.get<StudentScore>(`/predict/${studentId}/score`),

  getPortrait: (studentId: number) =>
    api.get<StudentPortraitDetail>(`/predict/${studentId}/portrait`),

  getRisk: (studentId: number) => api.get<RiskWarning>(`/predict/${studentId}/risk`),

  getSimulation: (studentId: number, subject = '数学') =>
    api.get<WhatIfResult[]>(`/predict/${studentId}/simulation?subject=${encodeURIComponent(subject)}`),

  getAdmissionLine: (schoolId: number, targetYear = 2026) =>
    api.get<ScoreLinePrediction>(
      `/admission-line/${schoolId}?target_year=${targetYear}`,
    ),

  getAdvice: (studentId: number) => api.get<AIAdvice>(`/advice/${studentId}`),
};
