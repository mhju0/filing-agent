export type Lang = "ko" | "en";
export type Intent = {
  companies: string[];
  metric: string | null;
  periods: string[];
  basis: string;
  action: string;
};
export type Source = {
  regulator: string;
  filing_title: string;
  filing_identity: string;
  url: string;
  section: string;
  link_status?: string;
  excerpt_cells?: string[];
  excerpt?: string;
  [key: string]: unknown;
};
export type Figure = {
  id: string;
  company: string;
  metric: string;
  period: string;
  period_start: string;
  period_end: string;
  value: string;
  currency: string;
  original_value: string;
  original_unit: string;
  source_label: string;
  basis: string;
  source: Source;
};
export type Answer = {
  operation: string;
  figures: Figure[];
  calculated: {
    inputs: string[];
    absolute_change: string;
    percentage_change: string;
    currency: string;
  }[];
  answer_ko: string;
  answer_en: string;
  reason_code: string | null;
  searched: {
    filing_title: string;
    section: string;
    company: string;
    period: string;
  }[];
};
export type Turn = {
  id: string;
  request_id: string;
  question: string;
  question_en?: string;
  language: Lang;
  status: string;
  created_at: string;
  wall_seconds?: number;
  intent?: Intent;
  answer?: Answer;
  error?: string;
  retry_of?: string;
  steps: {
    name: string;
    status: string;
    seconds?: number;
    started_at?: string;
    reused?: boolean;
  }[];
};
export type Investigation = {
  id: string;
  snapshot_id: string;
  saved: boolean;
  accepted: Intent | null;
  pending: Intent | null;
  turns: Turn[];
  created_at: string;
  lineage?: { mode: string; investigation_id: string } | null;
};
export type Replay = {
  schema: string;
  recorded_at: string;
  investigations: Investigation[];
};
