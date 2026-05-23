import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Play, Square, Upload, Loader2, ArrowLeft, Mic, FileText, HelpCircle, Wifi, WifiOff, Radio } from "lucide-react";
import DashboardLayout from "../layouts/DashboardLayout";
import { sessionsAPI, transcriptsAPI, questionsAPI, analyticsAPI } from "../services/api";
import type { Session, Transcript, Question, Analytics, LecturerInfo } from "../types/session";

const WS_BASE_URL = "wss://teachsense.onrender.com/ws";

type WSStatus = "disconnected" | "connecting" | "connected" | "error";

const SessionPage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const id = Number(sessionId);

  const [session, setSession] = useState<Session | null>(null);
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [transcriptText, setTranscriptText] = useState("");
  const [submittingTranscript, setSubmittingTranscript] = useState(false);

  // WebSocket state
  const [wsStatus, setWsStatus] = useState<WSStatus>("disconnected");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [liveQuestions, setLiveQuestions] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  const lecturerInfo: LecturerInfo | null = JSON.parse(
    localStorage.getItem("lecturerInfo") || "null"
  );

  const fetchAll = useCallback(async () => {
    if (!id) return;
    try {
      const [sessionRes, transcriptRes, questionsRes] = await Promise.all([
        sessionsAPI.getOne(id),
        transcriptsAPI.getAll(id),
        questionsAPI.getAll(id),
      ]);
      setSession(sessionRes.data);
      setTranscripts(transcriptRes.data);
      setQuestions(questionsRes.data);

      if (sessionRes.data.status === "completed") {
        try {
          const analyticsRes = await analyticsAPI.getSession(id);
          setAnalytics(analyticsRes.data);
        } catch {
          // analytics may not exist yet
        }
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  // ─── WebSocket Connection ─────────────────────────────
  const connectWebSocket = useCallback(() => {
    if (!lecturerInfo?.access || !id) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setWsStatus("connecting");

    const ws = new WebSocket(
      `${WS_BASE_URL}/sessions/${id}/?token=${lecturerInfo.access}`
    );
    wsRef.current = ws;

    ws.onopen = () => {
      setWsStatus("connected");
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "transcript.update":
            // Live transcript segment from hardware mic
            setLiveTranscript((prev) => prev + " " + data.transcript_segment);
            // Auto scroll to bottom
            setTimeout(() => {
              transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
            }, 100);
            break;

          case "question.generated":
            // New AI-generated question
            setLiveQuestions((prev) => [...prev, data.question]);
            break;

          case "analytics.update":
            // Live analytics update
            setAnalytics((prev) => ({ ...prev, ...data.analytics }));
            break;

          case "session.status":
            // Session status change
            setSession((prev) => prev ? { ...prev, status: data.status } : prev);
            if (data.status === "completed") fetchAll();
            break;

          default:
            console.log("WS message:", data);
        }
      } catch (err) {
        console.error("Failed to parse WS message:", err);
      }
    };

    ws.onerror = () => {
      setWsStatus("error");
    };

    ws.onclose = () => {
      setWsStatus("disconnected");
      wsRef.current = null;
    };
  }, [id, lecturerInfo?.access, fetchAll]);

  const disconnectWebSocket = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setWsStatus("disconnected");
  }, []);

  // Auto-connect when session is active
  useEffect(() => {
    if (session?.status === "active") {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }
    return () => disconnectWebSocket();
  }, [session?.status]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const updateStatus = async (status: string) => {
    try {
      await sessionsAPI.update(id, { status });
      fetchAll();
    } catch (error) {
      console.error(error);
    }
  };

  const submitTranscript = async () => {
    if (!transcriptText.trim()) return;
    setSubmittingTranscript(true);
    try {
      await transcriptsAPI.create(id, transcriptText);
      setTranscriptText("");
      fetchAll();
    } catch (error) {
      console.error("Failed to submit transcript:", error);
    } finally {
      setSubmittingTranscript(false);
    }
  };

  const uploadAudioFile = async (file: File) => {
    setUploading(true);
    try {
      const text = await file.text();
      await transcriptsAPI.create(id, text);
      fetchAll();
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setUploading(false);
    }
  };

  const wsStatusConfig = {
    disconnected: { color: "text-gray-400", bg: "bg-gray-100", icon: WifiOff, label: "Not connected" },
    connecting: { color: "text-amber-600", bg: "bg-amber-50", icon: Loader2, label: "Connecting..." },
    connected: { color: "text-emerald-600", bg: "bg-emerald-50", icon: Wifi, label: "Live" },
    error: { color: "text-red-500", bg: "bg-red-50", icon: WifiOff, label: "Connection error" },
  };

  const wsConfig = wsStatusConfig[wsStatus];
  const WSIcon = wsConfig.icon;

  return (
    <DashboardLayout title="Session Control">
      <div className="max-w-3xl mx-auto space-y-6">
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-[#2d9e3c] transition"
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
                  <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-1">Session</p>
                  <h1 className="text-2xl font-bold text-gray-900">{session.title}</h1>
                  <p className="text-sm text-gray-400 mt-1 font-mono">ID: {session.id}</p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className={`text-xs font-mono px-3 py-1 rounded-full border capitalize ${
                    session.status === "active"
                      ? "bg-emerald-100 text-emerald-700 border-emerald-200"
                      : session.status === "completed"
                      ? "bg-gray-100 text-gray-500 border-gray-200"
                      : "bg-amber-100 text-amber-700 border-amber-200"
                  }`}>
                    {session.status}
                  </span>

                  {/* WebSocket status badge */}
                  {session.status === "active" && (
                    <div className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1 rounded-full ${wsConfig.bg} ${wsConfig.color}`}>
                      <WSIcon size={11} className={wsStatus === "connecting" ? "animate-spin" : wsStatus === "connected" ? "animate-pulse" : ""} />
                      {wsConfig.label}
                    </div>
                  )}
                </div>
              </div>

              {session.status === "active" && (
                <div className="flex items-center justify-between mt-4 bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Mic size={15} className="text-emerald-600 animate-pulse" />
                    <span className="text-sm text-emerald-700 font-medium">
                      Session is live — recording in progress
                    </span>
                  </div>
                  {wsStatus !== "connected" && (
                    <button
                      onClick={connectWebSocket}
                      className="text-xs text-emerald-700 border border-emerald-200 px-3 py-1 rounded-lg hover:bg-emerald-100 transition"
                    >
                      Reconnect
                    </button>
                  )}
                </div>
              )}

              {analytics?.comprehension_score !== undefined && (
                <div className="mt-4 bg-gradient-to-r from-[#f0fdf4] to-[#e8fbed] border border-[#5cce6a]/20 rounded-xl px-5 py-4 flex items-center justify-between">
                  <span className="text-sm text-[#2d9e3c] font-medium">Comprehension Score</span>
                  <span className="text-3xl font-bold font-mono text-[#2d9e3c]">
                    {analytics.comprehension_score}%
                  </span>
                </div>
              )}
            </div>

            {/* Controls */}
            <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-4">Controls</p>
              <div className="flex flex-wrap gap-3">
                {session.status === "pending" && (
                  <button
                    onClick={() => updateStatus("active")}
                    className="flex items-center gap-2 bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white px-6 py-3 rounded-xl text-sm font-bold hover:from-[#3dae4c] hover:to-[#6cde7a] transition shadow-md shadow-green-200"
                  >
                    <Play size={15} fill="white" /> Start Session
                  </button>
                )}

                {session.status === "active" && (
                  <button
                    onClick={() => updateStatus("completed")}
                    className="flex items-center gap-2 bg-red-500 text-white px-6 py-3 rounded-xl text-sm font-bold hover:bg-red-600 transition"
                  >
                    <Square size={15} fill="white" /> End Session
                  </button>
                )}

                <label className="flex items-center gap-2 bg-gray-900 text-white px-6 py-3 rounded-xl text-sm font-medium cursor-pointer hover:bg-gray-700 transition">
                  {uploading ? <Loader2 size={15} className="animate-spin" /> : <Upload size={15} />}
                  {uploading ? "Processing..." : "Upload Transcript File"}
                  <input
                    type="file"
                    accept=".txt,.doc,.docx"
                    hidden
                    disabled={uploading}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) uploadAudioFile(file);
                    }}
                  />
                </label>
              </div>
            </div>

            {/* Live Transcript (WebSocket) */}
            {session.status === "active" && (
              <div className="bg-white border border-[#5cce6a]/20 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Radio size={15} className="text-[#2d9e3c] animate-pulse" />
                    <p className="text-xs font-mono text-[#2d9e3c] uppercase tracking-widest">Live Transcript</p>
                  </div>
                  {liveTranscript && (
                    <button
                      onClick={() => setLiveTranscript("")}
                      className="text-xs text-gray-400 hover:text-gray-600 transition"
                    >
                      Clear
                    </button>
                  )}
                </div>

                <div className="min-h-24 max-h-64 overflow-y-auto bg-[#f4faf5] rounded-xl p-4">
                  {liveTranscript ? (
                    <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {liveTranscript}
                    </p>
                  ) : (
                    <p className="text-sm text-gray-400 italic">
                      {wsStatus === "connected"
                        ? "Waiting for audio input from hardware device..."
                        : "Connect to WebSocket to see live transcript"}
                    </p>
                  )}
                  <div ref={transcriptEndRef} />
                </div>

                {/* Live questions from WebSocket */}
                {liveQuestions.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <p className="text-xs font-mono text-[#2d9e3c] uppercase tracking-widest">AI Generated Questions</p>
                    {liveQuestions.map((q, i) => (
                      <div key={i} className="bg-[#f0fdf4] border border-[#5cce6a]/20 rounded-xl p-3">
                        <p className="text-sm text-gray-700">{i + 1}. {q}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Manual Transcript Entry */}
            <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-3">Add Transcript Manually</p>
              <textarea
                rows={4}
                value={transcriptText}
                onChange={(e) => setTranscriptText(e.target.value)}
                placeholder="Paste or type lecture transcript here..."
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#5cce6a]/30 focus:border-[#5cce6a] transition resize-none"
              />
              <button
                onClick={submitTranscript}
                disabled={submittingTranscript || !transcriptText.trim()}
                className="mt-3 flex items-center gap-2 bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white px-5 py-2.5 rounded-xl text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed hover:from-[#3dae4c] hover:to-[#6cde7a] transition shadow-md shadow-green-200"
              >
                {submittingTranscript ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
                Submit Transcript
              </button>
            </div>

            {/* Saved Transcripts */}
            {transcripts.length > 0 && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <FileText size={15} className="text-[#2d9e3c]" />
                  <p className="text-xs font-mono text-gray-400 uppercase tracking-widest">Saved Transcripts</p>
                </div>
                {transcripts.map((t) => (
                  <p key={t.id} className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap mb-3 last:mb-0">
                    {t.content}
                  </p>
                ))}
              </div>
            )}

            {/* Questions */}
            {questions.length > 0 && (
              <div className="bg-[#f0fdf4] border border-[#5cce6a]/20 rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <HelpCircle size={15} className="text-[#2d9e3c]" />
                  <p className="text-xs font-mono text-[#2d9e3c] uppercase tracking-widest">Generated Questions</p>
                </div>
                <div className="space-y-3">
                  {questions.map((q, i) => (
                    <div key={q.id} className="bg-white rounded-xl p-4 border border-[#5cce6a]/10">
                      <p className="text-sm text-gray-700 font-medium">{i + 1}. {q.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Analytics Summary */}
            {analytics?.summary && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
                <p className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-3">AI Summary</p>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{analytics.summary}</p>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
};

export default SessionPage;