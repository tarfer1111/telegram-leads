// src/router/index.ts

import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth.store';

// --- Макеты (Layouts) ---
import AuthLayout from '@/layouts/AuthLayout.vue';
import DefaultLayout from '@/layouts/DefaultLayout.vue';

// --- Страницы (Views) ---
const LoginView = () => import('@/views/LoginView.vue');
const DashboardView = () => import('@/views/DashboardView.vue');
const LeadsView = () => import('@/views/LeadsView.vue');
const LeadDetailView = () => import('@/views/LeadDetailView.vue');
const ProjectsView = () => import('@/views/ProjectsView.vue');
// --- ДОБАВЛЕНО ---
const ProjectDetailView = () => import('@/views/ProjectDetailView.vue');
// --- КОНЕЦ ДОБАВЛЕНИЯ ---
const AdminManagersView = () => import('@/views/AdminManagersView.vue');
const NotFoundView = () => import('@/views/NotFoundView.vue');


// --- Определение роутов ---
const routes = [
    // --- Макет для страницы входа ---
    {
        path: '/login',
        component: AuthLayout,
        meta: { requiresAuth: false },
        children: [
            { path: '', name: 'login', component: LoginView }
        ]
    },

    // --- Основной макет админки ---
    {
        path: '/',
        component: DefaultLayout,
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                name: 'dashboard',
                component: DashboardView,
            },
            {
                path: 'leads',
                name: 'leads',
                component: LeadsView,
            },
            {
                path: 'leads/:id',
                name: 'lead-detail',
                component: LeadDetailView,
                props: true
            },
            {
                path: 'projects',
                name: 'projects',
                component: ProjectsView,
            },
            // --- ДОБАВЛЕНО ---
            {
                path: 'projects/:id', // Динамический роут для управления проектом
                name: 'project-detail',
                component: ProjectDetailView,
                props: true // Передавать :id как props в компонент
            },
            // --- КОНЕЦ ДОБАВЛЕНИЯ ---
            // --- Роут ТОЛЬКО ДЛЯ АДМИНА ---
            {
                path: 'admin/managers',
                name: 'admin-managers',
                component: AdminManagersView,
                meta: {
                    requiresAuth: true,
                    roles: ['admin']
                }
            },
        ]
    },

    // --- Страница 404 (Not Found) ---
    {
        path: '/:pathMatch(.*)*',
        name: 'not-found',
        component: NotFoundView
    }
];

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
});

// --- ГЛОБАЛЬНЫЙ СТРАЖ (Navigation Guard) ---
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();
    const isLoggedIn = authStore.isLoggedIn;
    const userRole = authStore.user?.role;
    const requiresAuth = to.meta.requiresAuth;
    const requiredRoles = to.meta.roles as string[] | undefined;

    if (to.name === 'login' && isLoggedIn) {
        next({ name: 'dashboard' });
        return;
    }
    if (requiresAuth && !isLoggedIn) {
        next({ name: 'login' });
        return;
    }
    if (requiredRoles && isLoggedIn) {
        if (userRole && requiredRoles.includes(userRole)) {
            next();
        } else {
            console.warn('Access denied. Missing required role.');
            next({ name: 'dashboard' });
        }
        return;
    }
    next();
});

export default router;