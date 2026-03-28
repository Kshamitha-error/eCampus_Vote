import axios from "axios";


// Development:  set REACT_APP_API_URL in .env.local
// Production:   set REACT_APP_API_URL in Vercel environment variables
const BASE = process.env.REACT_APP_API_URL || "http://192.168.0.21:5000/api";

const API = axios.create({
  baseURL: BASE,
  timeout: 15000,
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

API.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const url = err.config?.url || "";
      if (
        !url.includes("/auth/login") &&
        !url.includes("/auth/verify-identity") &&
        !url.includes("/auth/verify")
      ) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        localStorage.removeItem("role");
        window.location.href = "/";
      }
    }
    return Promise.reject(err);
  }
);

export default API;