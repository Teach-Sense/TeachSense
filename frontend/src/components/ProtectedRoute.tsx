import { Navigate } from "react-router-dom";

type Props = {
  children: React.ReactNode;
};


import { jwtDecode } from "jwt-decode";

const isTokenValid = (token: string | null) => {
  if (!token) return false;
  try {
    const decoded: any = jwtDecode(token);
    if (!decoded || !decoded.exp) return false;
    // Check if token is expired
    return decoded.exp * 1000 > Date.now();
  } catch {
    return false;
  }
};

const ProtectedRoute = ({ children }: Props) => {
  const token = localStorage.getItem("accessToken");
  if (!isTokenValid(token)) {
    // Optionally clear invalid tokens
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("lecturerInfo");
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export default ProtectedRoute;