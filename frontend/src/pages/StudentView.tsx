import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { Loader2, GraduationCap, FileText, BookOpen, HelpCircle } from "lucide-react";

const StudentView = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  type StudentSession = {
    title?: string;
    comprehensionScore?: number;
    summary?: string;
    transcript?: string;
    questions?: string;
  };
  const [session, setSession] = useState<StudentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const { data } = await axios.get(
          `http://localhost:5000/api/sessions/student/${sessionId}`
        );
        setSession(data);
      } catch {
        setError("Session not found or not yet available.");
      } finally {
        setLoading(false);
      }
    };

    fetchSession();
  }, [sessionId]);

  return (
    <div className="min-h-screen bg-[#f7f7f5]">
      {/* Header */}
      <div className="bg-[#0a0a0a] text-white px-8 py-5 flex items-center gap-3">
        <div className="w-8 h-8 bg-[#b8f729] rounded-lg flex items-center justify-center">
          <GraduationCap size={18} className="text-black" />
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
            {/* Session title */}
            <div>
              <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-1">
                Lecture Results
              </p>
              <h1 className="text-3xl font-bold text-gray-900">{session?.title ?? ""}</h1>
            </div>

            {/* Comprehension Score */}
            {session?.comprehensionScore !== undefined && (
              <div className="bg-[#0a0a0a] text-white rounded-2xl p-8 flex items-center justify-between">
                <div>
                  <p className="text-white/40 text-xs font-mono uppercase tracking-widest mb-2">
                    Class Comprehension Score
                  </p>
                  <p className="text-6xl font-bold font-mono text-[#b8f729]">
                    {session?.comprehensionScore ?? ""}%
                  </p>
                </div>
                <div className="text-white/10">
                  <BarChart size={64} />
                </div>
              </div>
            )}

            {/* Summary */}
            {session?.summary && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <BookOpen size={16} className="text-gray-400" />
                  <p className="text-xs font-mono text-gray-400 uppercase tracking-widest">
                    Lecture Summary
                  </p>
                </div>
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">
                  {session?.summary ?? ""}
                </p>
              </div>
            )}

            {/* Transcript */}
            {session?.transcript && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <FileText size={16} className="text-gray-400" />
                  <p className="text-xs font-mono text-gray-400 uppercase tracking-widest">
                    Full Transcript
                  </p>
                </div>
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm max-h-64 overflow-y-auto">
                  {session?.transcript ?? ""}
                </p>
              </div>
            )}

            {/* Questions */}
            {session?.questions && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <HelpCircle size={16} className="text-gray-400" />
                  <p className="text-xs font-mono text-gray-400 uppercase tracking-widest">
                    Generated Quiz Questions
                  </p>
                </div>
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">
                  {session?.questions ?? ""}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// Simple bar chart icon fallback
const BarChart = ({ size }: { size: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
    <rect x="3" y="12" width="4" height="9" rx="1" />
    <rect x="10" y="7" width="4" height="14" rx="1" />
    <rect x="17" y="3" width="4" height="18" rx="1" />
  </svg>
);

export default StudentView;