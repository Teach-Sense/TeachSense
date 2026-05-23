import { Navigate } from "react-router-dom";
import type { LecturerInfo } from "../types/session";

type Props = {
  children: React.ReactNode;
};

const ProtectedRoute = ({ children }: Props) => {
  const info: LecturerInfo | null = JSON.parse(
    localStorage.getItem("lecturerInfo") || "null"
  );

  if (!info?.access) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;