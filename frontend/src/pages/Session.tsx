import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Play, Square, Upload, Loader2, ArrowLeft, Mic } from "lucide-react";
import DashboardLayout from "../layouts/DashboardLayout";
import type { Session, LecturerInfo } from "../types/session";

const SessionPage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const lecturerInfo: LecturerInfo | null = JSON.parse(
    localStorage.getItem("lecturerInfo") || "null"
  );

  const authHeaders = useMemo(
    () => ({ Authorization: `Bearer ${lecturerInfo?.token}` }),
    [lecturerInfo?.token]
  );

  const fetchSession = useCallback(async () => {
    try {
      const { data } = await axios.get("http://localhost:5000/api/sessions", {
        headers: authHeaders,
      });
      const found = data.find((s: Session) => s._id === sessionId);
      setSession(found || null);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [authHeaders, sessionId]);

  const startSession = async () => {
    if (!sessionId) return;
    try {
      await axios.put(`http://localhost:5000/api/sessions/${sessionId}/start`, {}, { headers: authHeaders });
      fetchSession();
    } catch (error) {
      console.error(error);
    }
  };

  const endSession = async () => {
    if (!sessionId) return;
    try {
      await axios.put(`http://localhost:5000/api/sessions/${sessionId}/end`, {}, { headers: authHeaders });
      fetchSession();
    } catch (error) {
      console.error(error);
    }
  };

  const uploadAudio = async (file: File) => {
    if (!sessionId) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("audio", file);

      await axios.post(`http://localhost:5000/api/upload/${sessionId}`, formData, {
        headers: { ...authHeaders, "Content-Type": "multipart/form-data" },
      });

      fetchSession();
    } catch (error) {
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    setTimeout(() => {
      fetchSession();
    }, 0);
  }, [fetchSession]);

  return (
    <DashboardLayout title="Session Control">
      <div className="max-w-3xl mx-auto space-y-6">
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition"
        >
          <ArrowLeft size={15} /> Back to Dashboard
        </button>

        {loading ? (
          <div className="flex items-center justify-center py-20 text-gray-400">
            <Loader2 size={22} className="animate-spin mr-3" /> Loading session...
          </div>
        ) : !session ? (
          <div className="text-center py-20 text-gray-400">Session not found.</div>
        ) : (
          <>
            {/* Session Header */}
            <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-1">
                    Session
                  </p>
                  <h1 className="text-2xl font-bold text-gray-900">{session.title}</h1>
                  <p className="text-sm text-gray-400 mt-1 font-mono">ID: {session._id}</p>
                </div>

                <span
                  className={`text-xs font-mono px-3 py-1 rounded-full border capitalize ${
                    session.status === "active"
                      ? "bg-green-100 text-green-700 border-green-200"
                      : session.status === "completed"
                      ? "bg-gray-100 text-gray-500 border-gray-200"
                      : "bg-yellow-100 text-yellow-700 border-yellow-200"
                  }`}
                >
                  {session.status}
                </span>
              </div>

              {/* Live indicator */}
              {session.status === "active" && (
                <div className="flex items-center gap-2 mt-4 bg-green-50 border border-green-100 rounded-xl px-4 py-3">
                  <Mic size={15} className="text-green-600 animate-pulse" />
                  <span className="text-sm text-green-700 font-medium">
                    Session is live — recording in progress
                  </span>
                </div>
              )}
            </div>

            {/* Controls */}
            <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-4">
                Controls
              </p>
              <div className="flex flex-wrap gap-3">
                {session.status === "pending" && (
                  <button
                    onClick={startSession}
                    className="flex items-center gap-2 bg-[#b8f729] text-black px-6 py-3 rounded-xl text-sm font-bold hover:bg-[#c8ff30] transition"
                  >
                    <Play size={15} fill="black" /> Start Session
                  </button>
                )}

                {session.status === "active" && (
                  <button
                    onClick={endSession}
                    className="flex items-center gap-2 bg-red-500 text-white px-6 py-3 rounded-xl text-sm font-bold hover:bg-red-600 transition"
                  >
                    <Square size={15} fill="white" /> End Session
                  </button>
                )}

                <label className="flex items-center gap-2 bg-gray-900 text-white px-6 py-3 rounded-xl text-sm font-medium cursor-pointer hover:bg-gray-700 transition">
                  {uploading ? (
                    <Loader2 size={15} className="animate-spin" />
                  ) : (
                    <Upload size={15} />
                  )}
                  {uploading ? "Processing audio..." : "Upload Audio"}
                  <input
                    type="file"
                    accept="audio/*"
                    hidden
                    disabled={uploading}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) uploadAudio(file);
                    }}
                  />
                </label>
              </div>
            </div>

            {/* Results */}
            {session.transcript && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-3">
                  Transcript
                </p>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {session.transcript}
                </p>
              </div>
            )}

            {session.summary && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-3">
                  AI Summary
                </p>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {session.summary}
                </p>
              </div>
            )}

            {session.questions && (
              <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6">
                <p className="text-xs font-mono text-blue-400 uppercase tracking-widest mb-3">
                  Generated Quiz Questions
                </p>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {session.questions}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
};

export default SessionPage;