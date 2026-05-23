import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Play, Square, ChevronRight, Loader2, BookOpen, BarChart2, CheckCircle2 } from "lucide-react";
import DashboardLayout from "../layouts/DashboardLayout";
import StatCard from "../components/dashboard/StatCard";
import { sessionsAPI, dashboardAPI } from "../services/api";
import type { Session, DashboardOverview, LecturerInfo } from "../types/session";

const statusStyle: Record<string, string> = {
  active: "bg-emerald-100 text-emerald-700 border-emerald-200",
  completed: "bg-gray-100 text-gray-500 border-gray-200",
  pending: "bg-amber-100 text-amber-700 border-amber-200",
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const lecturerInfo: LecturerInfo | null = JSON.parse(
    localStorage.getItem("lecturerInfo") || "null"
  );

  useEffect(() => {
    if (!lecturerInfo?.access) navigate("/");
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const [sessionsRes, overviewRes] = await Promise.all([
        sessionsAPI.getAll(),
        dashboardAPI.getOverview(),
      ]);
      setSessions(sessionsRes.data);
      setOverview(overviewRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const createSession = async () => {
    if (!title.trim()) return;
    setCreating(true);
    try {
      const { data } = await sessionsAPI.create(title);
      setTitle("");
      setSessions((prev) => [data, ...prev]);
    } catch (error) {
      console.error("Failed to create session:", error);
    } finally {
      setCreating(false);
    }
  };

  const updateStatus = async (id: number, status: string) => {
    try {
      await sessionsAPI.update(id, { status });
      fetchData();
    } catch (error) {
      console.error(error);
    }
  };

  const completedSessions = sessions.filter((s) => s.status === "completed");

  return (
    <DashboardLayout title="Dashboard">
      <div className="max-w-5xl mx-auto space-y-8">

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            title="Total Sessions"
            value={String(sessions.length)}
            icon={<BookOpen size={16} />}
          />
          <StatCard
            title="Completed"
            value={String(completedSessions.length)}
            accent="text-[#2d9e3c]"
            icon={<CheckCircle2 size={16} />}
          />
          <StatCard
            title="Teaching Score"
            value={overview?.teaching_score ? `${overview.teaching_score}%` : "—"}
            accent="text-amber-600"
            icon={<BarChart2 size={16} />}
          />
        </div>

        {/* Create Session */}
        <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm">
          <h2 className="text-xs font-mono uppercase tracking-widest text-gray-400 mb-4">
            New Session
          </h2>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Enter lecture title e.g. Introduction to Ohm's Law"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && createSession()}
              className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#5cce6a]/30 focus:border-[#5cce6a] transition"
            />
            <button
              onClick={createSession}
              disabled={creating || !title.trim()}
              className="flex items-center gap-2 bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white px-5 py-3 rounded-xl text-sm font-bold hover:from-[#3dae4c] hover:to-[#6cde7a] transition disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-green-200"
            >
              {creating ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
              Create
            </button>
          </div>
        </div>

        {/* Sessions List */}
        <div>
          <h2 className="text-xs font-mono uppercase tracking-widest text-gray-400 mb-4">
            Lecture Sessions
          </h2>

          {loading ? (
            <div className="flex items-center justify-center py-16 text-gray-400">
              <Loader2 size={24} className="animate-spin mr-3" />
              Loading sessions...
            </div>
          ) : sessions.length === 0 ? (
            <div className="bg-white border border-dashed border-gray-200 rounded-2xl py-16 text-center text-gray-400">
              <BookOpen size={32} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">No sessions yet. Create your first lecture above.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="bg-white border border-gray-100 p-5 rounded-2xl shadow-sm hover:shadow-md transition-all hover:border-[#5cce6a]/20"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="text-base font-semibold text-gray-900 truncate">
                          {session.title}
                        </h3>
                        <span
                          className={`shrink-0 text-xs font-mono px-2 py-0.5 rounded-full border capitalize ${
                            statusStyle[session.status] ?? statusStyle.pending
                          }`}
                        >
                          {session.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 font-mono">
                        {new Date(session.created_at).toLocaleDateString("en-GB", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 shrink-0">
                      {session.status === "pending" && (
                        <button
                          onClick={() => updateStatus(session.id, "active")}
                          className="flex items-center gap-2 bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white px-4 py-2 rounded-lg text-xs font-bold hover:from-[#3dae4c] hover:to-[#6cde7a] transition"
                        >
                          <Play size={12} fill="white" />
                          Start
                        </button>
                      )}

                      {session.status === "active" && (
                        <button
                          onClick={() => updateStatus(session.id, "completed")}
                          className="flex items-center gap-2 bg-red-500 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-red-600 transition"
                        >
                          <Square size={12} fill="white" />
                          End
                        </button>
                      )}

                      {session.status === "completed" && (
                        <button
                          onClick={() => navigate(`/session/${session.id}`)}
                          className="flex items-center gap-2 border border-[#5cce6a]/30 text-[#2d9e3c] px-4 py-2 rounded-lg text-xs font-medium hover:bg-[#f0fdf4] transition"
                        >
                          View Results
                          <ChevronRight size={12} />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;