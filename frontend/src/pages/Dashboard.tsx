import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Play, Square, ChevronRight, Loader2, BookOpen, BarChart2, CheckCircle2 } from "lucide-react";
import DashboardLayout from "../layouts/DashboardLayout";
import StatCard from "../components/dashboard/StatCard";
import { sessionsAPI, dashboardAPI } from "../services/api";
import type { Session, DashboardMetrics } from "../types/session";

const statusStyle: Record<string, string> = {
  ongoing: "bg-emerald-100 text-emerald-700 border-emerald-200",
  completed: "bg-gray-100 text-gray-500 border-gray-200",
  scheduled: "bg-amber-100 text-amber-700 border-amber-200",
};
const fetchData = useCallback(async () => {
  setError(null);
  try {
    const sessionsRes = await sessionsAPI.getAll();
    const data = sessionsRes.data;
    const sessionsList = data.data?.results ?? data.results ?? data;
    setSessions(Array.isArray(sessionsList) ? sessionsList : []);

    try {
      const overviewRes = await dashboardAPI.getOverview();
      setMetrics(overviewRes.data.data ?? overviewRes.data);
    } catch {
      // metrics optional
    }
  } catch (err: any) {
    setError(
      err?.response?.status === 401
        ? "You are not authenticated. Please log in again."
        : `Failed to load dashboard: ${err?.response?.data?.detail || err?.message || "Unknown error"}`
    );
  } finally {
    setLoading(false);
  }
}, []);
const Dashboard = () => {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setError(null);
    try {
      const sessionsRes = await sessionsAPI.getAll();
      const data = sessionsRes.data;
      const sessionsList = data.data?.results ?? data.results ?? data;
      setSessions(Array.isArray(sessionsList) ? sessionsList : []);

      try {
        const dashRes = await dashboardAPI.getAll();
        const dashboards = dashRes.data.data?.results ?? dashRes.data.results ?? dashRes.data;
        if (Array.isArray(dashboards) && dashboards.length > 0) {
          const metricsRes = await dashboardAPI.getMetrics(dashboards[0].id);
          setMetrics(metricsRes.data.data ?? metricsRes.data);
        }
      } catch {
        // metrics optional
      }
    } catch (err: any) {
      setError(
        err?.response?.status === 401
          ? "You are not authenticated. Please log in again."
          : `Failed to load dashboard: ${err?.response?.data?.detail || err?.message || "Unknown error"}`
      );
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

  if (error) {
    return (
      <DashboardLayout title="Dashboard">
        <div className="max-w-5xl mx-auto p-4 sm:p-8 text-center">
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 sm:p-8">
            <h2 className="text-base sm:text-lg font-bold text-red-600 mb-2">{error}</h2>
            <button
              className="mt-4 px-6 py-2 bg-[#2d9e3c] text-white rounded-xl text-sm font-bold hover:bg-[#3dae4c] transition"
              onClick={() => fetchData()}
            >
              Try Again
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Dashboard">
      <div className="max-w-5xl mx-auto space-y-6 sm:space-y-8">

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 sm:gap-4">
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
            title="Avg Engagement"
            value={metrics?.avg_engagement ? `${metrics.avg_engagement}` : "—"}
            accent="text-amber-600"
            icon={<BarChart2 size={16} />}
          />
        </div>

        {/* Create Session */}
        <div className="bg-white border border-gray-100 p-4 sm:p-6 rounded-2xl shadow-sm">
          <h2 className="text-xs font-mono uppercase tracking-widest text-gray-400 mb-3 sm:mb-4">New Session</h2>
          <div className="flex flex-col sm:flex-row gap-3">
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
              className="flex items-center justify-center gap-2 bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white px-5 py-3 rounded-xl text-sm font-bold hover:from-[#3dae4c] hover:to-[#6cde7a] transition disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-green-200 shrink-0"
            >
              {creating ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
              Create
            </button>
          </div>
        </div>

        {/* Sessions List */}
        <div>
          <h2 className="text-xs font-mono uppercase tracking-widest text-gray-400 mb-3 sm:mb-4">Lecture Sessions</h2>

          {loading ? (
            <div className="flex items-center justify-center py-16 text-gray-400">
              <Loader2 size={24} className="animate-spin mr-3" /> Loading sessions...
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
                  className="bg-white border border-gray-100 p-4 sm:p-5 rounded-2xl shadow-sm hover:shadow-md transition-all hover:border-[#5cce6a]/20"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start gap-3 sm:gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <h3 className="text-base font-semibold text-gray-900 truncate">{session.title}</h3>
                        <span className={`shrink-0 text-xs font-mono px-2 py-0.5 rounded-full border capitalize ${statusStyle[session.status] ?? statusStyle.scheduled}`}>
                          {session.status}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400 font-mono">
                        {session.started_at && (
                          <span>{new Date(session.started_at).toLocaleDateString("en-GB", {
                            day: "numeric", month: "short", year: "numeric",
                          })}</span>
                        )}
                        {session.participant_count !== undefined && (
                          <span>· {session.participant_count} participants</span>
                        )}
                        {session.session_code && (
                          <span className="bg-gray-100 px-2 py-0.5 rounded-md">
                            Code: {session.session_code}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-row sm:flex-col gap-2 shrink-0">
                      {session.status === "scheduled" && (
                        <button
                          onClick={() => updateStatus(session.id, "ongoing")}
                          className="flex items-center gap-2 bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white px-4 py-2 rounded-lg text-xs font-bold hover:from-[#3dae4c] hover:to-[#6cde7a] transition"
                        >
                          <Play size={12} fill="white" /> Start
                        </button>
                      )}

                      {session.status === "ongoing" && (
                        <button
                          onClick={() => updateStatus(session.id, "completed")}
                          className="flex items-center gap-2 bg-red-500 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-red-600 transition"
                        >
                          <Square size={12} fill="white" /> End
                        </button>
                      )}

                      {session.status === "completed" && (
                        <button
                          onClick={() => navigate(`/session/${session.id}`)}
                          className="flex items-center gap-2 border border-[#5cce6a]/30 text-[#2d9e3c] px-4 py-2 rounded-lg text-xs font-medium hover:bg-[#f0fdf4] transition"
                        >
                          View Results <ChevronRight size={12} />
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