import { Navigate } from "react-router-dom";

type Props = {
  children: React.ReactNode;
};

const ProtectedRoute = ({ children }: Props) => {
  const token = localStorage.getItem("accessToken");
  if (!token) return <Navigate to="/" replace />;
  return <>{children}</>;
};

export default ProtectedRoute;