import { useEffect, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Plus, Play, Square, Upload, ChevronRight, Loader2, BookOpen, BarChart2 } from "lucide-react";
import DashboardLayout from "../layouts/DashboardLayout";
import StatCard from "../components/dashboard/StatCard";
import type { Session, LecturerInfo } from "../types/session";

const Dashboard = () => {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [uploadingId, setUploadingId] = useState<string | null>(null);

  const lecturerInfo: LecturerInfo | null = JSON.parse(
    localStorage.getItem("lecturerInfo") || "null"
  );

  // Safe redirect if no token
  useEffect(() => {
    if (!lecturerInfo?.token) {
      navigate("/");
    }
  }, [lecturerInfo?.token, navigate]);

  const authHeaders = useMemo(
    () => ({ Authorization: `Bearer ${lecturerInfo?.token}` }),
    [lecturerInfo?.token]
  );

  const fetchSessions = useCallback(async () => {
    if (!lecturerInfo?.token) return;
    try {
      const { data } = await axios.get("http://localhost:5000/api/sessions", {
        headers: authHeaders,
      });
      setSessions(data);
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
    } finally {
      setLoading(false);
    }
  }, [lecturerInfo?.token, authHeaders]);

  const createSession = async () => {
    if (!title.trim()) return;
    setCreating(true);
    try {
      await axios.post(
        "http://localhost:5000/api/sessions",
        { title },
        { headers: authHeaders }
      );
      setTitle("");
      await fetchSessions();
    } catch (error) {
      console.error("Failed to create session:", error);
    } finally {
      setCreating(false);
    }
  };

  const startSession = async (id: string) => {
    try {
      await axios.put(`http://localhost:5000/api/sessions/${id}/start`, {}, { headers: authHeaders });
      fetchSessions();
    } catch (error) {
      console.error(error);
    }
  };

  const endSession = async (id: string) => {
    try {
      await axios.put(`http://localhost:5000/api/sessions/${id}/end`, {}, { headers: authHeaders });
      fetchSessions();
    } catch (error) {
      console.error(error);
    }
  };

  const uploadAudio = async (id: string, file: File) => {
    setUploadingId(id);
    try {
      const formData = new FormData();
      formData.append("audio", file);

      await axios.post(`http://localhost:5000/api/upload/${id}`, formData, {
        headers: {
          ...authHeaders,
          "Content-Type": "multipart/form-data",
        },
      });

      fetchSessions();
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setUploadingId(null);
    }
  };

  useEffect(() => {
    setTimeout(() => {
      fetchSessions();
    }, 0);
  }, [fetchSessions]);

  const completedSessions = sessions.filter((s) => s.status === "completed");
  // const activeSessions = sessions.filter((s) => s.status === "active");

  const statusStyle = {
    active: "bg-green-100 text-green-700 border-green-200",
    completed: "bg-gray-100 text-gray-500 border-gray-200",
    pending: "bg-yellow-100 text-yellow-700 border-yellow-200",
  };

  return (
    <DashboardLayout title="Dashboard">
      <div className="max-w-5xl mx-auto space-y-8">

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            title="Total Sessions"
            value={String(sessions.length)}
            icon={<BookOpen size={18} />}
          />
          <StatCard
            title="Completed"
            value={String(completedSessions.length)}
            accent="text-[#2d7f3c]"
            icon={<BarChart2 size={18} />}
          />
          <StatCard
            title="Teaching Score"
            value={`${lecturerInfo?.teachingScore ?? 0}%`}
            accent="text-[#b8a000]"
          />
        </div>

        {/* Create Session */}
        <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm">
          <h2 className="text-sm font-mono uppercase tracking-widest text-gray-400 mb-4">
            New Session
          </h2>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Enter lecture title e.g. Introduction to Ohm's Law"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && createSession()}
              className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#b8f729]/40 focus:border-[#b8f729]"
            />
            <button
              onClick={createSession}
              disabled={creating || !title.trim()}
              className="flex items-center gap-2 bg-[#0a0a0a] text-white px-5 py-3 rounded-xl text-sm font-medium hover:bg-gray-800 transition disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {creating ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
              Create
            </button>
          </div>
        </div>

        {/* Sessions List */}
        <div>
          <h2 className="text-sm font-mono uppercase tracking-widest text-gray-400 mb-4">
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
                  key={session._id}
                  className="bg-white border border-gray-100 p-5 rounded-2xl shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="text-base font-semibold text-gray-900 truncate">
                          {session.title}
                        </h3>
                        <span
                          className={`shrink-0 text-xs font-mono px-2 py-0.5 rounded-full border capitalize ${
                            statusStyle[session.status as keyof typeof statusStyle]
                          }`}
                        >
                          {session.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 font-mono">
                        {new Date(session.createdAt).toLocaleDateString("en-GB", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>

                      {session.audioUrl && (
                        <p className="text-xs text-blue-500 font-mono mt-1">✓ Audio uploaded</p>
                      )}

                      {session.summary && (
                        <div className="mt-3 bg-gray-50 border border-gray-100 p-3 rounded-xl">
                          <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-1">
                            AI Summary
                          </p>
                          <p className="text-sm text-gray-700 line-clamp-3 whitespace-pre-wrap">
                            {session.summary}
                          </p>
                        </div>
                      )}

                      {session.questions && (
                        <div className="mt-3 bg-blue-50 border border-blue-100 p-3 rounded-xl">
                          <p className="text-xs font-mono text-blue-400 uppercase tracking-widest mb-1">
                            Quiz Questions
                          </p>
                          <p className="text-sm text-gray-700 line-clamp-3 whitespace-pre-wrap">
                            {session.questions}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 shrink-0">
                      {session.status === "pending" && (
                        <button
                          onClick={() => startSession(session._id)}
                          className="flex items-center gap-2 bg-[#b8f729] text-black px-4 py-2 rounded-lg text-xs font-bold hover:bg-[#c8ff30] transition"
                        >
                          <Play size={12} fill="black" />
                          Start
                        </button>
                      )}

                      {session.status === "active" && (
                        <button
                          onClick={() => endSession(session._id)}
                          className="flex items-center gap-2 bg-red-500 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-red-600 transition"
                        >
                          <Square size={12} fill="white" />
                          End
                        </button>
                      )}

                      <label className="flex items-center gap-2 bg-gray-900 text-white px-4 py-2 rounded-lg text-xs font-medium cursor-pointer hover:bg-gray-700 transition">
                        {uploadingId === session._id ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          <Upload size={12} />
                        )}
                        {uploadingId === session._id ? "Processing..." : "Upload Audio"}
                        <input
                          type="file"
                          accept="audio/*"
                          hidden
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) uploadAudio(session._id, file);
                          }}
                        />
                      </label>

                      {session.status === "completed" && (
                        <button
                          onClick={() => navigate(`/student/${session._id}`)}
                          className="flex items-center gap-2 border border-gray-200 text-gray-600 px-4 py-2 rounded-lg text-xs font-medium hover:bg-gray-50 transition"
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