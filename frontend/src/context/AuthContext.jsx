import { createContext, useContext, useState, useEffect } from "react";
import API from "../utils/api";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user,  setUser]  = useState(() => { try { return JSON.parse(localStorage.getItem("user")); } catch { return null; } });
  const [role,  setRole]  = useState(() => localStorage.getItem("role"));
  const [unreadCount, setUnreadCount] = useState(0);

  const loginStudent = (accessToken, studentData) => {
    localStorage.setItem("token", accessToken);
    localStorage.setItem("user",  JSON.stringify(studentData));
    localStorage.setItem("role",  "student");
    setToken(accessToken); setUser(studentData); setRole("student");
  };

  const loginAdmin = (accessToken) => {
    localStorage.setItem("token", accessToken);
    localStorage.setItem("role",  "admin");
    localStorage.removeItem("user");
    setToken(accessToken); setUser(null); setRole("admin");
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("role");
    setToken(null); setUser(null); setRole(null); setUnreadCount(0);
  };

  useEffect(() => {
    if (role === "student" && token) {
      API.get("/notifications/")
        .then(r => setUnreadCount(r.data.unread_count || 0))
        .catch(() => {});
    }
  }, [role, token]);

  return (
    <AuthContext.Provider value={{ token, user, role, loading:false, unreadCount, setUnreadCount, loginStudent, loginAdmin, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() { return useContext(AuthContext); }