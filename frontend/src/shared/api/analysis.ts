import { api } from '@/lib/api';

// 1:1 mirror of backend `app/agent/api/v1/analysis_router.py` and
// `report_router.py` + `student_router.py`, all mounted under `/api/v1/agent`.
//
// Note: the original frontend plan called for a single
// `POST /agent/analysis` endpoint returning a unified `AnalysisResponse`.
// The real backend exposes several per-feature endpoints
// (`/analysis/weak-points`, `/analysis/trends`, `/analysis/tiers`, ...),
// so `analyze()` below acts as a facade that fans out to the relevant
// endpoints in parallel and reshapes the results into the unified
// `AnalysisResponse` consumed by `/teacher/analysis`.

// -- Backend response types (1:1 with Pydantic) -------------------------------

export interface KPItem {
  kp_id: number;
  name: string;
  level: number;
  parent_id?: number | null;
  mastery_rate: number;
  class_avg_score: number;
  grade_avg_score: number;
  deviation: number;
  discrimination: number;
}

export interface WeakPointResponse {
  class_id: number;
  exam_ids: number[];
  knowledge_points: KPItem[];
  summary?: string;
}

export interface TrendSummaryResponse {
  class_id: number;
  exam_ids: number[];
  exam_avgs: number[];
  slope: number;
  direction: string;
  weak_kp_trends: Array<Record<string, unknown>>;
}

export interface ExamBrief {
  id: number;
  name: string;
  exam_date?: string;
  [key: string]: unknown;
}

interface ExamsResponse {
  class_id: number;
  exams: ExamBrief[];
}

export interface StudentBrief {
  id?: number;
  student_no: string;
  name: string;
  class_id?: number;
  [key: string]: unknown;
}

interface ClassStudentsResponse {
  class_id: number;
  students: StudentBrief[];
  count: number;
}

export interface ReportTaskCreated {
  task_id: string;
  status: string;
}

export interface ReportTaskStatus {
  task_id: string;
  status: string;
  progress?: number;
  result?: unknown;
  created_at?: string;
}

// -- Unified shape consumed by the analysis page ------------------------------

export type InsightLevel = 'info' | 'warning' | 'danger';

export interface AnalysisInsight {
  title: string;
  description: string;
  level?: InsightLevel;
}

export interface AnalysisTrendPoint {
  exam: string;
  avg: number;
  top?: number;
}

export interface AnalysisHeatmapPoint {
  x: number;
  y: number;
  value: number;
}

export interface AnalysisResponse {
  summary: string;
  insights: AnalysisInsight[];
  trends: AnalysisTrendPoint[];
  heatmap: AnalysisHeatmapPoint[];
  // Axis labels for the heatmap, derived from the data so the page doesn't
  // have to invent names when the real KP names come from the backend.
  heatmapXLabels: string[];
  heatmapYLabels: string[];
}

// -- Input contracts ----------------------------------------------------------

export interface AnalyzeRequest {
  class_id: number;
  /** Optional explicit exam IDs. If omitted, all class exams are fetched. */
  exam_ids?: number[];
  /**
   * Optional exam name to filter to a single exam. Resolved against the
   * backend's `/analysis/exams/{class_id}` list before any analysis call.
   */
  exam_name?: string;
}

export interface ReportRequest {
  class_id: number;
  class_name?: string;
  exam_ids: number[];
  modules?: string[];
}

// -- Internal helpers ---------------------------------------------------------

// Classify a knowledge point by mastery rate. Matches the bands the analysis
// page filters by ("warning" + "danger" → risk list).
function classifyMastery(rate: number): InsightLevel {
  if (rate < 0.5) return 'danger';
  if (rate < 0.7) return 'warning';
  return 'info';
}

// -- API client ---------------------------------------------------------------

export const analysisApi = {
  /** List all exams the backend has for a class, for the exam picker. */
  async listExams(classId: number): Promise<ExamBrief[]> {
    const res = await api.get<ExamsResponse>(`/agent/analysis/exams/${classId}`);
    return res.exams;
  },

  /** Raw weak-point endpoint (kept exposed for callers that need the full payload). */
  weakPoints: (data: { class_id: number; exam_ids: number[]; kp_ids?: number[] }) =>
    api.post<WeakPointResponse>('/agent/analysis/weak-points', data),

  /** Raw trends endpoint. Backend requires at least 2 exam_ids. */
  trends: (data: { class_id: number; exam_ids: number[] }) =>
    api.post<TrendSummaryResponse>('/agent/analysis/trends', data),

  /**
   * Unified analysis call used by the /teacher/analysis page. Fans out to
   * weak-points + trends and reshapes results into `AnalysisResponse`.
   *
   * The fan-out is fully best-effort: any sub-call that fails (e.g. trends
   * with only 1 exam, weak-points on a class with no data) is swallowed and
   * the corresponding slice of the response stays empty. The page renders
   * its own fallbacks for empty heatmap / trends.
   */
  async analyze(req: AnalyzeRequest): Promise<AnalysisResponse> {
    let examIds = req.exam_ids ?? [];
    let exams: ExamBrief[] = [];

    if (examIds.length === 0 || req.exam_name) {
      exams = await analysisApi.listExams(req.class_id).catch(() => []);
      if (req.exam_name) {
        const match = exams.find((e) => e.name === req.exam_name);
        examIds = match ? [match.id] : [];
      } else if (examIds.length === 0) {
        examIds = exams.map((e) => e.id);
      }
    }

    // We need at least 2 exams for trends and at least 1 for weak-points.
    const wpExamIds = examIds.length > 0 ? examIds : [];
    const trendExamIds = examIds.length >= 2 ? examIds : [];

    const [wpResult, trendResult] = await Promise.all([
      wpExamIds.length > 0
        ? analysisApi.weakPoints({ class_id: req.class_id, exam_ids: wpExamIds }).catch(() => null)
        : Promise.resolve(null),
      trendExamIds.length >= 2
        ? analysisApi.trends({ class_id: req.class_id, exam_ids: trendExamIds }).catch(() => null)
        : Promise.resolve(null),
    ]);

    // Summary: prefer weak-points summary, else trend direction.
    const summary =
      wpResult?.summary?.trim() ||
      (trendResult
        ? `班级整体趋势: ${trendResult.direction} (斜率 ${trendResult.slope.toFixed(2)})`
        : '');

    // Insights: top-N weakest KPs become warning/danger entries.
    const insights: AnalysisInsight[] = (wpResult?.knowledge_points ?? [])
      .slice()
      .sort((a, b) => a.mastery_rate - b.mastery_rate)
      .slice(0, 6)
      .map((kp) => ({
        title: kp.name,
        description: `掌握率 ${(kp.mastery_rate * 100).toFixed(1)}% · 班均 ${kp.class_avg_score.toFixed(1)} / 年级 ${kp.grade_avg_score.toFixed(1)}`,
        level: classifyMastery(kp.mastery_rate),
      }));

    // Trends: exam_avgs paired with exam names from the lookup (or a fallback
    // index-based label if names aren't available). `top` is unknown from
    // this endpoint so we omit it.
    const trendExams = exams.length > 0 ? exams : [];
    const trendPoints: AnalysisTrendPoint[] = (trendResult?.exam_avgs ?? []).map((avg, i) => {
      const examId = trendResult?.exam_ids?.[i];
      const exam = trendExams.find((e) => e.id === examId);
      return {
        exam: exam?.name ?? `考试${i + 1}`,
        avg: Number.isFinite(avg) ? Number(avg.toFixed(2)) : 0,
      };
    });

    // Heatmap: KP × exam matrix of mastery rates (×100 so the gradient is 0-100).
    // Since the weak-points endpoint aggregates across exam_ids and only
    // returns one row per KP, we render a single-column heatmap when there's
    // just one exam, or duplicate the column across exams when multiple are
    // requested. This stays honest about backend granularity without forcing
    // the page to invent data.
    const kps = (wpResult?.knowledge_points ?? []).slice(0, 10);
    const heatmapYLabels = kps.map((kp) => kp.name);
    const heatmapXLabels =
      examIds.length > 0 ? examIds.map((id) => {
        const e = trendExams.find((x) => x.id === id);
        return e?.name ?? `考试${id}`;
      }) : [];
    const heatmap: AnalysisHeatmapPoint[] = [];
    kps.forEach((kp, y) => {
      const value = Math.round(kp.mastery_rate * 100);
      heatmapXLabels.forEach((_, x) => {
        heatmap.push({ x, y, value });
      });
    });

    return {
      summary,
      insights,
      trends: trendPoints,
      heatmap,
      heatmapXLabels,
      heatmapYLabels,
    };
  },

  /**
   * Submit a comprehensive report task. Returns a `task_id` that callers
   * can poll via `reportStatus`. Backend is async (202 + task_id).
   */
  async report(req: ReportRequest): Promise<ReportTaskCreated> {
    return api.post<ReportTaskCreated>('/agent/reports/generate', {
      class_id: req.class_id,
      class_name: req.class_name ?? '未知班级',
      exam_ids: req.exam_ids,
      modules: req.modules ?? ['weak-points', 'tiered-teaching', 'student-lists'],
    });
  },

  /** Poll the status of an async report task. */
  reportStatus: (taskId: string) =>
    api.get<ReportTaskStatus>(`/agent/reports/${taskId}`),

  /** List students in a class (mirrors the same call in `agent.ts`). */
  async listStudents(classId: number): Promise<StudentBrief[]> {
    const res = await api.get<ClassStudentsResponse>(`/agent/students/class/${classId}`);
    return res.students;
  },
};
