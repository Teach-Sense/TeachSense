import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { ChevronRight, Loader2, Clock, BookOpen } from "lucide-react";
import DashboardLayout from "../layouts/DashboardLayout";
import type { Session, LecturerInfo } from "../types/session";

const History = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  const lecturerInfo: LecturerInfo | null = JSON.parse(
    localStorage.getItem("lecturerInfo") || "null"
  );

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const { data } = await axios.get("http://localhost:5000/api/sessions", {
          headers: { Authorization: `Bearer ${lecturerInfo?.token}` },
        });
        // Show only completed sessions in history
        setSessions(data.filter((s: Session) => s.status === "completed"));
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, [lecturerInfo?.token]);

  return (
    <DashboardLayout title="Lecture History">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Lecture History</h1>
            <p className="text-sm text-gray-400 mt-1">All completed sessions</p>
          </div>
          <span className="text-xs font-mono bg-gray-100 text-gray-500 px-3 py-1 rounded-full">
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
                key={session._id}
                className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center shrink-0">
                      <BookOpen size={16} className="text-gray-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{session.title}</h3>
                      <p className="text-xs text-gray-400 font-mono mt-0.5">
                        {new Date(session.createdAt).toLocaleDateString("en-GB", {
                          weekday: "short",
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {session.comprehensionScore !== undefined && (
                      <div className="text-right">
                        <p className="text-xs text-gray-400 font-mono">Comprehension</p>
                        <p className="text-lg font-bold text-[#2d7f3c] font-mono">
                          {session.comprehensionScore}%
                        </p>
                      </div>
                    )}
                    <button
                      onClick={() => navigate(`/student/${session._id}`)}
                      className="flex items-center gap-1 text-xs text-gray-500 border border-gray-200 px-3 py-2 rounded-xl hover:bg-gray-50 transition"
                    >
                      View <ChevronRight size={12} />
                    </button>
                  </div>
                </div>

                {session.summary && (
                  <div className="mt-3 pl-14">
                    <p className="text-sm text-gray-500 line-clamp-2">{session.summary}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default History;