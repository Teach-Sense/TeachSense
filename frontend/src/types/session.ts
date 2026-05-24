// Auth
export type LecturerInfo = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  avatar_url?: string;
};

// Sessions
export type SessionStatus = "scheduled" | "ongoing" | "completed";

export type Session = {
  id: number;
  title: string;
  description?: string;
  status: SessionStatus;
  started_at?: string;
  ended_at?: string;
  created_at?: string;
  scheduled_at?: string;
  participant_count?: number;
  questions_count?: number;
  responses_count?: number;
  transcript?: string;
  session_code?: string;
  ws_url?: string;
};

// Paginated response
export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

// Transcripts
export type Transcript = {
  id: number;
  session_id: number;
  content: string;
  speaker: string;
  timestamp: string;
  status: string;
  created_at: string;
};

// Questions
export type Question = {
  id: number;
  session_id: number;
  text: string;
  asker_name?: string;
  status: "pending" | "answered" | "archived";
  answer?: string;
  answer_timestamp?: string;
  upvotes: number;
  created_at: string;
};

// Responses
export type Response = {
  id: number;
  question_id: number;
  student_id: number;
  text: string;
  status: string;
  feedback?: string;
  score?: number;
  created_at: string;
};

// Devices
export type Device = {
  id: number;
  name: string;
  type: string;
  protocol: string;
  status: string;
  auth_token?: string;
  last_heartbeat?: string;
  ws_url?: string;
};

// Analytics
export type Analytics = {
  session_id: number;
  total_participants: number;
  avg_engagement_score: number;
  questions_asked: number;
  responses_submitted: number;
  avg_response_time: number;
  participation_rate: number;
};

// Dashboard
export type DashboardMetrics = {
  current_sessions: number;
  active_participants: number;
  avg_engagement: number;
  system_health: string;
};