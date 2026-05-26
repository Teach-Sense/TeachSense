import { useNavigate } from "react-router-dom";
import { GraduationCap, Mic, Brain, BarChart2, Cpu } from "lucide-react";

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">

      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-[#2d9e3c] rounded-xl flex items-center justify-center">
            <GraduationCap size={18} className="text-white" />
          </div>
          <span className="font-mono font-bold text-lg">TeachSense</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/login")}
            className="px-5 py-2 text-sm border border-white/10 rounded-xl text-white/70 hover:text-white hover:bg-white/5 transition"
          >
            Sign In
          </button>
          <button
            onClick={() => navigate("/register")}
            className="px-5 py-2 text-sm bg-[#2d9e3c] rounded-xl font-medium hover:bg-[#3dae4c] transition"
          >
            Register
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center px-8 py-16 max-w-6xl mx-auto w-full">
        <div>
          <p className="text-[#5cce6a] text-xs font-mono uppercase tracking-widest mb-5">
            Classroom Intelligence
          </p>
          <h1 className="text-5xl font-bold leading-tight mb-6">
            Turn lectures into
            <br />
            <span className="text-[#5cce6a]">measurable insights.</span>
          </h1>
          <p className="text-white/40 text-base leading-relaxed mb-8 max-w-md">
            Capture, transcribe, and analyse every session in real time.
            Track teaching effectiveness and student comprehension over time.
          </p>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/register")}
              className="px-7 py-3 bg-[#2d9e3c] text-white font-bold rounded-xl hover:bg-[#3dae4c] transition shadow-lg shadow-green-900/30"
            >
              Get started free
            </button>
            <button
              onClick={() => navigate("/login")}
              className="px-7 py-3 border border-white/10 text-white/70 rounded-xl hover:text-white hover:bg-white/5 transition"
            >
              Sign in →
            </button>
          </div>
          <div className="flex items-center gap-6 mt-10">
            {["Speech-to-Text", "AI Summaries", "Quiz Generation"].map((tag) => (
              <div key={tag} className="flex items-center gap-2 text-white/20 text-xs font-mono">
                <div className="w-1 h-1 rounded-full bg-[#5cce6a]/40" />
                {tag}
              </div>
            ))}
          </div>
        </div>

        {/* Faceless illustration */}
        <div className="relative bg-[#0d1f0f] border border-[#1a3d1c] rounded-2xl p-8 flex flex-col items-center justify-center min-h-[340px] overflow-hidden">
          <div className="absolute top-0 right-0 w-48 h-48 bg-[#2d9e3c]/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-32 h-32 bg-[#5cce6a]/5 rounded-full blur-2xl" />

          <div className="relative z-10 w-20 h-20 rounded-full border-2 border-[#2d9e3c] flex items-center justify-center bg-[#071a09] mb-4">
            <Mic size={32} className="text-[#5cce6a]" />
          </div>

          <div className="flex items-center gap-2 mb-5 z-10">
            <div className="w-2 h-2 bg-[#5cce6a] rounded-full animate-pulse" />
            <span className="text-[#5cce6a]/70 text-xs font-mono">Session is live</span>
          </div>

          <div className="flex items-end gap-1.5 z-10 mb-6">
            {[8, 18, 28, 16, 24, 12, 20, 10, 22, 14].map((h, i) => (
              <div
                key={i}
                className="w-1.5 bg-[#2d9e3c] rounded-full"
                style={{
                  height: `${h}px`,
                  animation: `waveBar 1s ease-in-out ${i * 0.1}s infinite alternate`,
                }}
              />
            ))}
          </div>

          <div className="flex items-center gap-3 z-10">
            <div className="bg-[#0a0a0a] border border-white/10 rounded-full px-4 py-1.5 text-xs font-mono text-white/50">
              <span className="text-[#5cce6a] font-bold">24</span> students
            </div>
            <div className="bg-[#0a0a0a] border border-white/10 rounded-full px-4 py-1.5 text-xs font-mono text-white/50">
              <span className="text-[#5cce6a] font-bold">87%</span> engagement
            </div>
          </div>

          <style>{`
            @keyframes waveBar {
              from { transform: scaleY(0.4); }
              to { transform: scaleY(1); }
            }
          `}</style>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-white/5 px-8 py-12">
        <p className="text-white/20 text-xs font-mono uppercase tracking-widest text-center mb-8">
          What TeachSense does
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-4xl mx-auto">
          {[
            { icon: <Mic size={18} className="text-[#2d9e3c]" />, title: "Speech to text", desc: "Live transcription of every lecture powered by AI speech recognition." },
            { icon: <Brain size={18} className="text-[#2d9e3c]" />, title: "AI summaries", desc: "Automatic lecture summaries and key takeaways generated after each session." },
            { icon: <BarChart2 size={18} className="text-[#2d9e3c]" />, title: "Analytics", desc: "Track comprehension scores, participation rates, and engagement over time." },
          ].map(({ icon, title, desc }) => (
            <div key={title} className="bg-[#0d1f0f] border border-[#1a3d1c] rounded-2xl p-6 hover:border-[#2d9e3c]/40 transition">
              <div className="w-9 h-9 bg-[#2d9e3c]/10 rounded-xl flex items-center justify-center mb-4">{icon}</div>
              <h3 className="font-semibold text-sm mb-2">{title}</h3>
              <p className="text-white/40 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu size={12} className="text-[#5cce6a]" />
          <span className="text-white/20 text-xs font-mono">System online</span>
          <div className="w-1.5 h-1.5 bg-[#5cce6a] rounded-full animate-pulse ml-1" />
        </div>
        <span className="text-white/20 text-xs font-mono">TeachSense · Classroom Intelligence System</span>
      </footer>

    </div>
  );
};

export default Landing;