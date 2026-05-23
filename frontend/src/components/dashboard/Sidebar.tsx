import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard,  Clock, GraduationCap } from "lucide-react";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/history", label: "History", icon: Clock },
];

const Sidebar = () => {
  const location = useLocation();

  return (
    <div className="w-64 bg-[#0a0a0a] text-white min-h-screen flex flex-col p-6 border-r border-white/5">
      {/* Logo */}
      <div className="mb-10 flex items-center gap-3">
        <div className="w-8 h-8 bg-[#b8f729] rounded-lg flex items-center justify-center">
          <GraduationCap size={18} className="text-black" />
        </div>
        <h1 className="text-xl font-bold tracking-tight font-mono">TeachSense</h1>
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
                  ? "bg-[#b8f729] text-black"
                  : "text-white/50 hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="border-t border-white/5 pt-4">
        <div className="flex items-center gap-2 px-4 py-2">
          <div className="w-2 h-2 rounded-full bg-[#b8f729] animate-pulse" />
          <span className="text-white/30 text-xs font-mono">SYSTEM ONLINE</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;