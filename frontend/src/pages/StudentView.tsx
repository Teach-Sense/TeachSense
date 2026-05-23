import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Loader2, GraduationCap, FileText, BookOpen, HelpCircle, TrendingUp } from "lucide-react";
import { sessionsAPI, transcriptsAPI, questionsAPI, analyticsAPI } from "../services/api";
import type { Session, Transcript, Question, Analytics } from "../types/session";

const StudentView = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const id = Number(sessionId);

  const [session, setSession] = useState<Session | null>(null);
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [sessionRes, transcriptRes, questionsRes] = await Promise.all([
          sessionsAPI.getOne(id),
          transcriptsAPI.getAll(id),
          questionsAPI.getAll(id),
        ]);
        setSession(sessionRes.data);
        setTranscripts(transcriptRes.data);
        setQuestions(questionsRes.data);

        try {
          const analyticsRes = await analyticsAPI.getSession(id);
          setAnalytics(analyticsRes.data);
        } catch {
          // analytics optional
        }
      } catch {
        setError("Session not found or not yet available.");
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [id]);

  return (
    <div className="min-h-screen bg-[#f4faf5]">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#0d1f0f] to-[#071a09] text-white px-8 py-5 flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-br from-[#5cce6a] to-[#2d9e3c] rounded-lg flex items-center justify-center">
          <GraduationCap size={18} className="text-white" />
        </div>
        <h1 className="font-mono font-bold text-lg">TeachSense</h1>
        <span className="text-white/30 font-mono text-sm ml-2">/ Student Results</span>
      </div>

      <div className="max-w-4xl mx-auto p-8 space-y-6">
        {loading ? (
          <div className="flex items-center justify-center py-24 text-gray-400">
            <Loader2 size={24} className="animate-spin mr-3" /> Loading results...
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-600 rounded-2xl p-8 text-center">
            <p>{error}</p>
          </div>
        ) : (
          <>
            {/* Title */}
            <div>
              <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-1">Lecture Results</p>
              <h1 className="text-3xl font-bold text-gray-900">{session?.title}</h1>
            </div>

            {/* Comprehension Score */}
            {analytics?.comprehension_score !== undefined && (
              <div className="bg-gradient-to-br from-[#0d1f0f] to-[#071a09] text-white rounded-2xl p-8 flex items-center justify-between">
                <div>
                  <p className="text-white/40 text-xs font-mono uppercase tracking-widest mb-2">
                    Class Comprehension Score
                  </p>
                  <p className="text-6xl font-bold font-mono text-[#5cce6a]">
                    {analytics.comprehension_score}%
                  </p>
                </div>
                <TrendingUp size={64} className="text-white/10" />
              </div>
            )}

            {/* Summary */}
            {analytics?.summary && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <BookOpen size={16} className="text-[#2d9e3c]" />
                  <p className="text-xs font-mono text-gray-400 uppercase tracking-widest">Lecture Summary</p>
                </div>
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">
                  {analytics.summary}
                </p>
              </div>
            )}

            {/* Transcripts */}
            {transcripts.length > 0 && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <FileText size={16} className="text-[#2d9e3c]" />
                  <p className="text-xs font-mono text-gray-400 uppercase tracking-widest">Full Transcript</p>
                </div>
                <div className="max-h-64 overflow-y-auto space-y-3">
                  {transcripts.map((t) => (
                    <p key={t.id} className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">
                      {t.content}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Questions */}
            {questions.length > 0 && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <HelpCircle size={16} className="text-[#2d9e3c]" />
                  <p className="text-xs font-mono text-gray-400 uppercase tracking-widest">Quiz Questions</p>
                </div>
                <div className="space-y-3">
                  {questions.map((q, i) => (
                    <div key={q.id} className="bg-[#f0fdf4] border border-[#5cce6a]/20 rounded-xl p-4">
                      <p className="text-sm text-gray-800 font-medium">{i + 1}. {q.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default StudentView;