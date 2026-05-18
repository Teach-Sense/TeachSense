type Props = {
  title: string;
  value: string;
  accent?: string;
  icon?: React.ReactNode;
};

const StatCard = ({ title, value, accent = "text-gray-900", icon }: Props) => {
  return (
    <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-xs font-mono text-gray-400 uppercase tracking-widest">{title}</h3>
        {icon && <div className="text-gray-300">{icon}</div>}
      </div>
      <p className={`text-4xl font-bold font-mono ${accent}`}>{value}</p>
    </div>
  );
};

export default StatCard;