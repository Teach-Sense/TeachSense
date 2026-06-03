import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { GraduationCap, AlertCircle, Eye, EyeOff } from "lucide-react";
import { authAPI, getErrorMessage } from "../services/api";

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  
  const handleLogin = async (e: React.FormEvent) => {
  e.preventDefault();
  setError("");
  setLoading(true);

  try {
    const { data } = await authAPI.login(username, password);
    const responseData = data?.data ?? data;
    const access = responseData?.access;
    const refresh = responseData?.refresh;
    const user = responseData?.user;

    if (!access || !refresh) {
      throw new Error("Invalid login response");
    }

    localStorage.setItem("accessToken", access);
    localStorage.setItem("refreshToken", refresh);
    if (user && typeof user === "object") {
      localStorage.setItem("lecturerInfo", JSON.stringify(user));
    } else {
      localStorage.removeItem("lecturerInfo");
    }
    navigate("/dashboard");
  } catch (err) {
    setError(getErrorMessage(err as { response?: { data?: unknown } }));
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="min-h-screen bg-[#071a09] flex animate-fade-in">
      {/* Left panel */}
      <div className="hidden lg:flex w-1/2 flex-col justify-between p-12 border-r border-[#1a3d1c] relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="absolute top-20 left-20 w-64 h-64 bg-[#2d9e3c]/10 rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-10 w-48 h-48 bg-[#5cce6a]/8 rounded-full blur-2xl" />
        </div>

        <div className="relative flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-[#5cce6a] to-[#2d9e3c] rounded-xl flex items-center justify-center shadow-lg shadow-green-900/50">
            <GraduationCap size={20} className="text-white" />
          </div>
          <span className="text-white font-mono font-bold text-xl">TeachSense</span>
        </div>

        <div className="relative">
          <p className="text-[#5cce6a]/50 text-xs font-mono uppercase tracking-widest mb-6">
            Classroom Intelligence
          </p>
          <h2 className="text-5xl font-bold text-white leading-tight mb-6">
            Turn lectures into
            <br />
            <span className="text-[#5cce6a]">measurable insights.</span>
          </h2>
          <p className="text-white/40 text-base leading-relaxed max-w-sm">
            Capture, transcribe, and analyse every session. Track teaching effectiveness over time.
          </p>
        </div>

        <div className="relative flex gap-6">
          {["Speech-to-Text", "AI Summaries", "Quiz Generation"].map((tag) => (
            <div key={tag} className="flex items-center gap-2 text-white/20 text-xs font-mono">
              <div className="w-1 h-1 rounded-full bg-[#5cce6a]/40" />
              {tag}
            </div>
          ))}
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-8 bg-[#0a0a0a]">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-8 lg:hidden">
              <div className="w-8 h-8 bg-gradient-to-br from-[#5cce6a] to-[#2d9e3c] rounded-lg flex items-center justify-center">
                <GraduationCap size={18} className="text-white" />
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

          <form onSubmit={handleLogin} className="space-y-4 animate-stagger">
            <div>
              <label className="block text-white/40 text-xs font-mono uppercase tracking-widest mb-2">
                Username
              </label>
              <input
                type="text"
                placeholder="dr_ahmad_zubair"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/20 outline-none focus:border-[#5cce6a]/50 transition-all text-sm"
              />
            </div>

            <div>
              <label className="block text-white/40 text-xs font-mono uppercase tracking-widest mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 pr-11 text-white placeholder:text-white/20 outline-none focus:border-[#5cce6a]/50 transition-all text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white py-3 rounded-xl font-bold text-sm hover:from-[#3dae4c] hover:to-[#6cde7a] transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2 shadow-lg shadow-green-900/30"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="text-center text-white/30 text-sm mt-6">
            Don't have an account?{" "}
            <Link to="/register" className="text-[#5cce6a] hover:text-[#7dde8a] transition font-medium">
              Register
            </Link>
          </p>

          <p className="text-white/20 text-xs font-mono text-center mt-8">
            TeachSense · Classroom Intelligence System
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;