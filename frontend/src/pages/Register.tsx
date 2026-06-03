import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { GraduationCap, AlertCircle, Eye, EyeOff } from "lucide-react";
import { authAPI, getErrorMessage } from "../services/api";

const Register = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== passwordConfirm) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      // Step 1: Register
      await authAPI.register(username, email, password, passwordConfirm);

      // Step 2: Auto login using USERNAME (not email!)
      const { data } = await authAPI.login(username, password);
      const responseData = data?.data ?? data;

      // Step 3: Store tokens and user info
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
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-8 animate-fade-in">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-9 h-9 bg-gradient-to-br from-[#5cce6a] to-[#2d9e3c] rounded-xl flex items-center justify-center shadow-lg shadow-green-900/50">
            <GraduationCap size={18} className="text-white" />
          </div>
          <span className="text-white font-mono font-bold text-lg">TeachSense</span>
        </div>

        <h1 className="text-3xl font-bold text-white mb-2">Create account</h1>
        <p className="text-white/40 text-sm mb-8">Join the TeachSense lecturer portal</p>

        {error && (
          <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl mb-6 text-sm">
            <AlertCircle size={16} className="shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-4 animate-stagger">
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
              Email
            </label>
            <input
              type="email"
              placeholder="lecturer@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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
                minLength={8}
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

          <div>
            <label className="block text-white/40 text-xs font-mono uppercase tracking-widest mb-2">
              Confirm Password
            </label>
            <div className="relative">
              <input
                type={showConfirm ? "text" : "password"}
                placeholder="••••••••"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                required
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 pr-11 text-white placeholder:text-white/20 outline-none focus:border-[#5cce6a]/50 transition-all text-sm"
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition"
              >
                {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {passwordConfirm && (
              <p className={`text-xs mt-1 ${password === passwordConfirm ? "text-[#5cce6a]" : "text-red-400"}`}>
                {password === passwordConfirm ? "✓ Passwords match" : "✗ Passwords do not match"}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || password !== passwordConfirm}
            className="w-full bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white py-3 rounded-xl font-bold text-sm hover:from-[#3dae4c] hover:to-[#6cde7a] transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2 shadow-lg shadow-green-900/30"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="text-center text-white/30 text-sm mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-[#5cce6a] hover:text-[#7dde8a] transition font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;