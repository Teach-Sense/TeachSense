import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Clock, GraduationCap, Cpu } from "lucide-react";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/history", label: "History", icon: Clock },
];

const Sidebar = () => {
  const location = useLocation();

  return (
    <div className="w-64 bg-[#0d1f0f] text-white min-h-screen flex flex-col p-6 border-r border-[#1a3d1c]">
      {/* Logo */}
      <div className="mb-10 flex items-center gap-3">
        <div className="w-9 h-9 bg-gradient-to-br from-[#5cce6a] to-[#2d9e3c] rounded-xl flex items-center justify-center shadow-lg shadow-green-900/40">
          <GraduationCap size={18} className="text-white" />
        </div>
        <h1 className="text-xl font-bold tracking-tight font-mono text-white">TeachSense</h1>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1 flex-1">
        {navItems.map(({ to, label, icon: Icon }) => {
          const isActive = location.pathname === to;
          return (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-150 ${
                isActive
                  ? "bg-gradient-to-r from-[#2d9e3c] to-[#3dbf4e] text-white shadow-md shadow-green-900/30"
                  : "text-white/40 hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="border-t border-[#1a3d1c] pt-4">
        <div className="flex items-center gap-2 px-4 py-2">
          <Cpu size={12} className="text-[#5cce6a]" />
          <span className="text-[#5cce6a]/50 text-xs font-mono">SYSTEM ONLINE</span>
          <div className="w-1.5 h-1.5 rounded-full bg-[#5cce6a] animate-pulse ml-auto" />
        </div>
      </div>
    </div>
  );
};

export default Sidebar;