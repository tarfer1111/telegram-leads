import axios from 'axios';
import { useAuthStore } from "@/stores/auth.store";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',

    headers: {
        'Content-Type': 'application/json'
    }
});

api.interceptors.request.use(
    (config) => {
        const authStore = useAuthStore();
        const token = authStore.token;

        if (token) {
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
        if (error.response && error.response.status === 401) {
            const authStore = useAuthStore();

            if (error.config.url !== '/managers/login') {
                console.error('Unauthorized access (401). Logging out.');

                authStore.logout();

                window.location.href = '/login';
            }
        }

        return Promise.reject(error);
    }
);

export default api;