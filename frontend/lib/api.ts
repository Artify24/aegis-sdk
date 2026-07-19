import axios from "axios";
import { toast } from "sonner";

export const api = axios.create({
  baseURL: "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("aegis_access_token") : null;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      if (typeof window !== "undefined") {
        try {
          const refreshToken = localStorage.getItem("aegis_refresh_token");
          if (refreshToken) {
            const res = await axios.post("http://localhost:8000/api/auth/refresh", null, {
              headers: { Authorization: `Bearer ${refreshToken}` }
            });
            const newAccessToken = res.data.access_token;
            localStorage.setItem("aegis_access_token", newAccessToken);
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return axios(originalRequest);
          }
        } catch (e) {
          localStorage.removeItem("aegis_access_token");
          localStorage.removeItem("aegis_refresh_token");
          localStorage.removeItem("aegis_user");
          window.location.href = "/login";
        }
      }
    } else if (error.response?.status >= 500) {
      toast.error("Internal Server Error. Please try again later.");
    } else if (error.message === "Network Error") {
      toast.error("Network Error. Please check your connection to the server.");
    }

    return Promise.reject(error);
  }
);
