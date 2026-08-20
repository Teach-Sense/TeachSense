import { useEffect, useRef, useState } from "react";
import { Mic, Volume2, RotateCcw } from "lucide-react";

type Phase = "idle" | "recording" | "processing" | "results";

const MOCK_RESULT = {
  overall: 78,
  comprehension: 82,
  scope: 68,
  revisit: [
    { topic: "Kirchhoff's Voltage Law", note: "Students paused on sign conventions — walk the loop direction explicitly next time." },
    { topic: "Series vs. Parallel Resistance", note: "Fewer questions here — comprehension was strong, keep pace." },
  ],
  topActions: [
    "Recap Ohm's Law with a worked numeric example before moving to KVL.",
    "Pause for a comprehension check every ~8 minutes — gaps clustered mid-lecture.",
    "Use a circuit diagram on-screen when introducing loop direction; verbal-only explanation lost several students.",
  ],
};

function formatTime(totalSeconds: number) {
  const m = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const s = (totalSeconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

function RadialGauge({ value }: { value: number }) {
  const size = 160;
  const stroke = 12;
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;
  const sweep = 0.75;
  const arcLength = circumference * sweep;
  const filled = arcLength * (value / 100);
  const rotation = 135;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#EAF6EC"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${arcLength} ${circumference}`}
          transform={`rotate(${rotation} ${size / 2} ${size / 2})`}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="url(#gaugeGradient)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          transform={`rotate(${rotation} ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dasharray 1s cubic-bezier(0.16, 1, 0.3, 1)" }}
        />
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#2d9e3c" />
            <stop offset="100%" stopColor="#5cce6a" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold tabular-nums text-[#2d9e3c]">{value}</span>
        <span className="text-[10px] tracking-[0.2em] uppercase text-gray-400 mt-0.5">Overall</span>
      </div>
    </div>
  );
}

const LectureConsole = () => {
  const [topic, setTopic] = useState("");
  const [className, setClassName] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const canStart = topic.trim().length > 0 && className.trim().length > 0;

  useEffect(() => {
    if (phase === "recording") {
      intervalRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [phase]);

  const handleToggleRecording = () => {
    if (phase === "idle") {
      setElapsed(0);
      setPhase("recording");
    } else if (phase === "recording") {
      setPhase("processing");
      setTimeout(() => setPhase("results"), 2600);
    }
  };

  const handleReset = () => {
    setPhase("idle");
    setElapsed(0);
    setTopic("");
    setClassName("");
  };

  return (
    <div className="min-h-screen bg-[#f4faf5]">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Lecture Console</h1>
          <p className="text-sm text-gray-400 mt-1">Record, generate questions, and review teaching effectiveness</p>
        </div>

        {/* Input strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          <div>
            <label className="block text-xs font-mono uppercase tracking-widest text-gray-400 mb-2">
              Lecture Topic
            </label>
            <input
              type="text"
              disabled={phase !== "idle"}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Introduction to Ohm's Law"
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#5cce6a]/30 focus:border-[#5cce6a] transition disabled:opacity-50 disabled:bg-gray-50"
            />
          </div>
          <div>
            <label className="block text-xs font-mono uppercase tracking-widest text-gray-400 mb-2">
              Class Taught
            </label>
            <input
              type="text"
              disabled={phase !== "idle"}
              value={className}
              onChange={(e) => setClassName(e.target.value)}
              placeholder="e.g. SS2 Physics"
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#5cce6a]/30 focus:border-[#5cce6a] transition disabled:opacity-50 disabled:bg-gray-50"
            />
          </div>
        </div>

        {/* Recording card */}
        <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-8 sm:p-10 flex flex-col items-center mb-6">
          <button
            onClick={handleToggleRecording}
            disabled={!canStart && phase === "idle"}
            className="relative w-28 h-28 sm:w-32 sm:h-32 rounded-full flex items-center justify-center transition disabled:opacity-30 disabled:cursor-not-allowed"
            style={{
              background:
                phase === "recording"
                  ? "linear-gradient(135deg, #ef4444, #f87171)"
                  : "linear-gradient(135deg, #2d9e3c, #5cce6a)",
              boxShadow:
                phase === "recording"
                  ? "0 0 0 8px rgba(239,68,68,0.12), 0 8px 24px -6px rgba(239,68,68,0.4)"
                  : "0 8px 24px -6px rgba(45,158,60,0.35)",
            }}
          >
            {phase === "recording" && (
              <span className="absolute inset-0 rounded-full animate-ping bg-red-400/30" />
            )}
            <Mic size={36} className="text-white" strokeWidth={1.75} />
          </button>

          <p className="mt-5 text-3xl font-mono tabular-nums text-gray-800">{formatTime(elapsed)}</p>

          {/* Waveform */}
          <div className="flex items-end gap-[3px] h-6 mt-3">
            {Array.from({ length: 28 }).map((_, i) => (
              <span
                key={i}
                className="w-[3px] rounded-full"
                style={{
                  height: phase === "recording" ? `${18 + Math.abs(Math.sin(i * 1.3)) * 82}%` : "12%",
                  background: phase === "recording" ? "#ef4444" : "#e5e7eb",
                  transition: "height 0.2s ease, background 0.3s ease",
                }}
              />
            ))}
          </div>

          <p
            className={`mt-6 text-xs uppercase tracking-widest font-mono font-semibold ${
              phase === "recording" ? "text-red-500" : "text-gray-400"
            }`}
          >
            {phase === "idle" && (canStart ? "Ready" : "Enter topic & class to begin")}
            {phase === "recording" && "● Recording"}
            {phase === "processing" && "Generating questions…"}
            {phase === "results" && "Session complete"}
          </p>

          {(phase === "idle" || phase === "recording") && (
            <button
              onClick={handleToggleRecording}
              disabled={!canStart}
              className="mt-6 flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-bold text-white transition disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
              style={{
                background:
                  phase === "recording"
                    ? "linear-gradient(135deg, #ef4444, #f87171)"
                    : "linear-gradient(135deg, #2d9e3c, #5cce6a)",
              }}
            >
              {phase === "recording" ? "Stop Recording" : "Start Recording"}
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-400 font-mono mb-8 px-1">
          <Volume2 size={13} />
          <span>Questions relay to the speaker after processing</span>
        </div>

        {/* Processing */}
        {/* Score — always on the board, starts at 0%, fills in once results are ready */}
        <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6 sm:p-8 mb-4">
          <div className="flex items-center justify-between mb-5">
            <p className="text-xs font-mono uppercase tracking-widest text-gray-400">
              Teaching Effectiveness
            </p>
            {phase === "processing" && (
              <span className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-gray-400">
                <span className="w-3.5 h-3.5 border-2 border-[#5cce6a]/30 border-t-[#2d9e3c] rounded-full animate-spin" />
                Scoring…
              </span>
            )}
          </div>

          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 sm:gap-8">
            <RadialGauge value={phase === "results" ? MOCK_RESULT.overall : 0} />
            <div className="flex-1 w-full space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-gray-500">Student Comprehension</span>
                  <span className="font-mono text-gray-700">{phase === "results" ? MOCK_RESULT.comprehension : 0}%</span>
                </div>
                <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${phase === "results" ? MOCK_RESULT.comprehension : 0}%`,
                      background: "linear-gradient(90deg, #2d9e3c, #5cce6a)",
                    }}
                  />
                </div>
                <p className="text-[10px] text-gray-400 font-mono mt-1">weight 70%</p>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-gray-500">Teaching Scope</span>
                  <span className="font-mono text-gray-700">{phase === "results" ? MOCK_RESULT.scope : 0}%</span>
                </div>
                <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${phase === "results" ? MOCK_RESULT.scope : 0}%`,
                      background: "linear-gradient(90deg, #f59e0b, #fbbf24)",
                    }}
                  />
                </div>
                <p className="text-[10px] text-gray-400 font-mono mt-1">weight 30%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tips — only appear once the score has actually been generated */}
        {phase === "results" && (
          <div className="space-y-4">
            <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6 sm:p-8">
              <p className="text-xs font-mono uppercase tracking-widest text-gray-400 mb-4">
                Topics To Revisit
              </p>
              <div className="space-y-4 mb-7">
                {MOCK_RESULT.revisit.map((r, i) => (
                  <div key={i} className="border-l-2 border-[#5cce6a] pl-4">
                    <p className="text-sm font-semibold text-gray-900">{r.topic}</p>
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed">{r.note}</p>
                  </div>
                ))}
              </div>

              <p className="text-xs font-mono uppercase tracking-widest text-gray-400 mb-4">
                Top 3 Actions
              </p>
              <ol className="space-y-3">
                {MOCK_RESULT.topActions.map((action, i) => (
                  <li key={i} className="flex gap-3.5 text-sm">
                    <span className="shrink-0 w-6 h-6 rounded-full bg-[#eafbee] text-[#2d9e3c] text-xs font-mono font-bold flex items-center justify-center mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-gray-700 leading-relaxed pt-0.5">{action}</span>
                  </li>
                ))}
              </ol>
            </div>

            <button
              onClick={handleReset}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl text-sm font-medium text-gray-500 border border-gray-200 hover:border-[#5cce6a]/40 hover:text-[#2d9e3c] hover:bg-[#f0fdf4] transition"
            >
              <RotateCcw size={14} />
              Start New Session
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default LectureConsole;