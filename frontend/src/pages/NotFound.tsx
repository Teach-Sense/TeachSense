import { useNavigate } from "react-router-dom";

export default function NotFound() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center text-white">
      <p className="text-[#b8f729] font-mono text-sm uppercase tracking-widest mb-4">Error 404</p>
      <h1 className="text-6xl font-bold mb-4">Page not found</h1>
      <p className="text-white/40 mb-8">The page you're looking for doesn't exist.</p>
      <button
        onClick={() => navigate("/")}
        className="bg-[#b8f729] text-black px-6 py-3 rounded-xl font-bold text-sm hover:bg-[#c8ff30] transition"
      >
        Go Home
      </button>
    </div>
  );
}