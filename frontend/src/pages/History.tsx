import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronRight, Loader2, Clock, BookOpen } from "lucide-react";
import DashboardLayout from "../layouts/DashboardLayout";
import { sessionsAPI } from "../services/api";
import type { Session } from "../types/session";

const History = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const { data } = await sessionsAPI.getAll();
        setSessions(data.filter((s: Session) => s.status === "completed"));
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchSessions();
  }, []);

  return (
    <DashboardLayout title="Lecture History">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Lecture History</h1>
            <p className="text-sm text-gray-400 mt-1">All completed sessions</p>
          </div>
          <span className="text-xs font-mono bg-[#f0fdf4] text-[#2d9e3c] border border-[#5cce6a]/20 px-3 py-1 rounded-full">
            {sessions.length} sessions
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20 text-gray-400">
            <Loader2 size={22} className="animate-spin mr-3" /> Loading history...
          </div>
        ) : sessions.length === 0 ? (
          <div className="bg-white border border-dashed border-gray-200 rounded-2xl py-20 text-center text-gray-400">
            <Clock size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No completed sessions yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md hover:border-[#5cce6a]/20 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-[#e8fbed] to-[#c6f5d0] rounded-xl flex items-center justify-center shrink-0">
                      <BookOpen size={16} className="text-[#2d9e3c]" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{session.title}</h3>
                      <p className="text-xs text-gray-400 font-mono mt-0.5">
                        {new Date(session.created_at).toLocaleDateString("en-GB", {
                          weekday: "short",
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => navigate(`/session/${session.id}`)}
                    className="flex items-center gap-1 text-xs text-[#2d9e3c] border border-[#5cce6a]/30 px-3 py-2 rounded-xl hover:bg-[#f0fdf4] transition"
                  >
                    View <ChevronRight size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default History;