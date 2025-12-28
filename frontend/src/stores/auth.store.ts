import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';

import type {
    ManagerResponse,
    LoginResponse,
    LoginRequestForm
} from '@/types/api.types';

export const useAuthStore = defineStore('auth', () => {
    const token = ref<string | null>(localStorage.getItem('token'));

    const user = ref<ManagerResponse | null>(
        JSON.parse(localStorage.getItem('user') || 'null')
    );

    const router = useRouter();

    const isLoggedIn = computed(() => !!token.value && !!user.value);

    const isAdmin = computed(() => user.value?.role === 'admin');

    const userFullName = computed(() => user.value?.full_name || 'User');

    async function login(loginForm: LoginRequestForm) {
        const formData = new URLSearchParams();
        formData.append('username', loginForm.username);
        formData.append('password', loginForm.password);
        formData.append('grant_type', 'password');

        try {
            const response = await api.post<LoginResponse>(
                '/auth/login',
                formData,
                {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                }
            );

            const { access_token, user: userData } = response.data;

            token.value = access_token;
            user.value = userData;

            localStorage.setItem('token', access_token);
            localStorage.setItem('user', JSON.stringify(userData));

            router.push({ name: 'leads' });

        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }

    function logout() {
        token.value = null;
        user.value = null;

        localStorage.removeItem('token');
        localStorage.removeItem('user');

        router.push({ name: 'login' });
    }

    async function fetchMe() {
        if (!isLoggedIn.value) return;

        try {
            const response = await api.get<ManagerResponse>('/managers/me');

            user.value = response.data;
            localStorage.setItem('user', JSON.stringify(response.data));

        } catch (error) {
            console.error('Failed to fetch user data:', error);
        }
    }

    return {
        token,
        user,
        isLoggedIn,
        isAdmin,
        userFullName,
        login,
        logout,
        fetchMe,
    };
});