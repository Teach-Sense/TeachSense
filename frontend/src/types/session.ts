// Auth
export type TokenPair = {
  access: string;
  refresh: string;
};

export type LecturerInfo = {
  id: number;
  name: string;
  email: string;
  access: string;
  refresh: string;
};

// Sessions
export type SessionStatus = "pending" | "active" | "completed";

export type Session = {
  id: number;
  title: string;
  status: SessionStatus;
  created_at: string;
  updated_at?: string;
};

// Transcripts
export type Transcript = {
  id: number;
  session: number;
  content: string;
  created_at: string;
};

// Questions
export type Question = {
  id: number;
  session: number;
  text: string;
  created_at: string;
};

// Responses
export type Response = {
  id: number;
  question: number;
  session: number;
  text: string;
  created_at: string;
};

// Analytics
export type Analytics = {
  session_id: number;
  comprehension_score?: number;
  summary?: string;
  total_questions?: number;
  total_responses?: number;
};

// Dashboard overview
export type DashboardOverview = {
  total_sessions: number;
  completed_sessions: number;
  teaching_score?: number;
};