import { useNavigate } from "react-router-dom";
import { LogOut, User } from "lucide-react";
import { authAPI } from "../../services/api";
import type { LecturerInfo } from "../../types/session";

type Props = {
  title?: string;
};

const Topbar = ({ title = "Dashboard" }: Props) => {
  const navigate = useNavigate();

  const lecturerInfo: LecturerInfo | null = JSON.parse(
    localStorage.getItem("lecturerInfo") || "null"
  );

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch {
      // ignore errors
    } finally {
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("lecturerInfo");
      navigate("/");
    }
  };

  const fullName = lecturerInfo
    ? `${lecturerInfo.first_name} ${lecturerInfo.last_name}`.trim() || lecturerInfo.email
    : "Lecturer";

  return (
    <div className="bg-white border-b border-gray-100 px-8 py-4 flex justify-between items-center">
      <div className="flex items-center gap-3">
        <div className="w-1 h-6 bg-gradient-to-b from-[#2d9e3c] to-[#5cce6a] rounded-full" />
        <h2 className="text-lg font-semibold text-gray-800 font-mono tracking-tight">{title}</h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3 bg-gray-50 border border-gray-100 rounded-xl px-4 py-2">
          <div className="w-7 h-7 bg-gradient-to-br from-[#2d9e3c] to-[#5cce6a] rounded-lg flex items-center justify-center">
            <User size={13} className="text-white" />
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-gray-800 leading-none">{fullName}</p>
            <p className="text-xs text-gray-400 mt-0.5">{lecturerInfo?.email}</p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-red-500 transition-colors px-3 py-2 rounded-xl hover:bg-red-50 border border-transparent hover:border-red-100"
        >
          <LogOut size={15} />
          Logout
        </button>
      </div>
    </div>
  );
};

export default Topbar;