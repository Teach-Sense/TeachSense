export type Session = {
  _id: string;
  title: string;
  status: "pending" | "active" | "completed";
  audioUrl?: string;
  transcript?: string;
  summary?: string;
  questions?: string;
  comprehensionScore?: number;
  createdAt: string;
};

export type LecturerInfo = {
  _id: string;
  name: string;
  email: string;
  token: string;
  teachingScore?: number;
};