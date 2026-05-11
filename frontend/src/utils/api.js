import axios from "axios";

// ✏️ ONLY CHANGE THIS LINE — paste your ngrok URL every day
const BASE_URL = "http://10.64.101.206:5000";

// — nothing else to touch below this line —
const BASE = BASE_URL + "/api";

export function getImageUrl(path) {
  if (!path) return "";
  
  // Handle full URLs — strip whatever host and replace with current BASE_URL
  if (path.includes("://")) {
    try {
      const u = new URL(path);
      return BASE_URL + u.pathname + "?ngrok-skip-browser-warning=true";
    } catch {
      return BASE_URL + "?ngrok-skip-browser-warning=true";
    }
  }
  
  // Handle relative paths like /uploads/abc.jpg
  const cleanPath = path.startsWith("/") ? path : "/" + path;
  return BASE_URL + cleanPath + "?ngrok-skip-browser-warning=true";
}

const API = axios.create({
  baseURL: BASE,
  timeout: 15000,
  headers: {
    "ngrok-skip-browser-warning": "true",
  },
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