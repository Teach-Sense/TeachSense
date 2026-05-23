import Sidebar from "../components/dashboard/Sidebar";
import Topbar from "../components/dashboard/Topbar";

type Props = {
  children: React.ReactNode;
  title?: string;
};

const DashboardLayout = ({ children, title }: Props) => {
  return (
    <div className="flex min-h-screen bg-[#f4faf5]">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Topbar title={title} />
        <main className="flex-1 p-8 overflow-auto">{children}</main>
      </div>
    </div>
  );
};

export default DashboardLayout;