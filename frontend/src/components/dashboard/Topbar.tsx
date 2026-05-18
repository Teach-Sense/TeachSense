import { useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";

type Props = {
  title?: string;
};

const Topbar = ({ title = "Dashboard" }: Props) => {
  const navigate = useNavigate();

  const lecturerInfo = JSON.parse(
    localStorage.getItem("lecturerInfo") || "null"
  );

  const handleLogout = () => {
    localStorage.removeItem("lecturerInfo");
    navigate("/");
  };

  return (
    <div className="bg-white border-b border-gray-100 px-8 py-4 flex justify-between items-center">
      <h2 className="text-lg font-semibold text-gray-800 font-mono tracking-tight">
        {title}
      </h2>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-sm font-semibold text-gray-800">
            {lecturerInfo?.name || "Lecturer"}
          </p>
          <p className="text-xs text-gray-400">{lecturerInfo?.email}</p>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-500 transition-colors px-3 py-2 rounded-lg hover:bg-red-50"
        >
          <LogOut size={15} />
          Logout
        </button>
      </div>
    </div>
  );
};

export default Topbar;