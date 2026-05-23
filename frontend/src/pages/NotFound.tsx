import { useNavigate } from "react-router-dom";
import { GraduationCap } from "lucide-react";

export default function NotFound() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[#071a09] flex flex-col items-center justify-center text-white">
      <div className="w-12 h-12 bg-gradient-to-br from-[#5cce6a] to-[#2d9e3c] rounded-2xl flex items-center justify-center mb-8 shadow-lg shadow-green-900/50">
        <GraduationCap size={24} className="text-white" />
      </div>
      <p className="text-[#5cce6a] font-mono text-sm uppercase tracking-widest mb-4">Error 404</p>
      <h1 className="text-6xl font-bold mb-4">Page not found</h1>
      <p className="text-white/40 mb-8">The page you're looking for doesn't exist.</p>
      <button
        onClick={() => navigate("/")}
        className="bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white px-6 py-3 rounded-xl font-bold text-sm hover:from-[#3dae4c] hover:to-[#6cde7a] transition shadow-lg shadow-green-900/30"
      >
        Go Home
      </button>
    </div>
  );
}