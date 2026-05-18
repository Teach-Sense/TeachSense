import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { GraduationCap, AlertCircle } from "lucide-react";

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { data } = await axios.post(
        "http://localhost:5000/api/auth/login",
        { email, password }
      );

      localStorage.setItem("lecturerInfo", JSON.stringify(data));
      navigate("/dashboard");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.message || "Login failed. Please try again.");
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex">
      {/* Left panel */}
      <div className="hidden lg:flex w-1/2 flex-col justify-between p-12 border-r border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-[#b8f729] rounded-xl flex items-center justify-center">
            <GraduationCap size={20} className="text-black" />
          </div>
          <span className="text-white font-mono font-bold text-xl">TeachSense</span>
        </div>

        <div>
          <p className="text-white/20 text-xs font-mono uppercase tracking-widest mb-4">
            Classroom Intelligence
          </p>
          <h2 className="text-5xl font-bold text-white leading-tight">
            Turn lectures into
            <br />
            <span className="text-[#b8f729]">measurable insights.</span>
          </h2>
          <p className="text-white/40 mt-4 text-base leading-relaxed max-w-sm">
            Capture, transcribe, and analyse every session. Track teaching effectiveness over time.
          </p>
        </div>

        <div className="flex gap-8">
          {["Speech-to-Text", "AI Summaries", "Quiz Generation"].map((tag) => (
            <div key={tag} className="text-white/20 text-xs font-mono">
              ✦ {tag}
            </div>
          ))}
        </div>
      </div>

      {/* Right panel - Login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-8 lg:hidden">
              <div className="w-8 h-8 bg-[#b8f729] rounded-lg flex items-center justify-center">
                <GraduationCap size={18} className="text-black" />
              </div>
              <span className="text-white font-mono font-bold">TeachSense</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Welcome back</h1>
            <p className="text-white/40 text-sm">Sign in to your lecturer portal</p>
          </div>

          {error && (
            <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl mb-6 text-sm">
              <AlertCircle size={16} className="shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-white/50 text-xs font-mono uppercase tracking-widest mb-2">
                Email
              </label>
              <input
                type="email"
                placeholder="lecturer@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/20 outline-none focus:border-[#b8f729]/50 focus:bg-white/8 transition-all text-sm"
              />
            </div>

            <div>
              <label className="block text-white/50 text-xs font-mono uppercase tracking-widest mb-2">
                Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/20 outline-none focus:border-[#b8f729]/50 transition-all text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#b8f729] text-black py-3 rounded-xl font-bold text-sm hover:bg-[#c8ff30] transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="text-white/20 text-xs font-mono text-center mt-8">
            TeachSense · Classroom Intelligence System
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;