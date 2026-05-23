type Props = {
  title: string;
  value: string;
  accent?: string;
  icon?: React.ReactNode;
  trend?: string;
};

const StatCard = ({ title, value, accent = "text-gray-900", icon, trend }: Props) => {
  return (
    <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5 duration-200">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-xs font-mono text-gray-400 uppercase tracking-widest">{title}</h3>
        {icon && (
          <div className="w-8 h-8 bg-gradient-to-br from-[#e8fbed] to-[#c6f5d0] rounded-lg flex items-center justify-center text-[#2d9e3c]">
            {icon}
          </div>
        )}
      </div>
      <p className={`text-4xl font-bold font-mono ${accent}`}>{value}</p>
      {trend && (
        <p className="text-xs text-[#2d9e3c] font-mono mt-2 flex items-center gap-1">
          <span>↑</span> {trend}
        </p>
      )}
    </div>
  );
};

export default StatCard;