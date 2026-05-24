import { Navigate } from "react-router-dom";

type Props = {
  children: React.ReactNode;
};

const ProtectedRoute = ({ children }: Props) => {
  const info = JSON.parse(localStorage.getItem("lecturerInfo") || "null");

  if (!info?.email) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;