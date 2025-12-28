<script lang="ts" setup>
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth.store';

const authStore = useAuthStore();
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar__logo">
      CRM Leads
    </div>
    <nav class="sidebar__nav">
      <RouterLink :to="{ name: 'leads' }" class="nav-link">
        Лиды
      </RouterLink>
      <div v-if="authStore.isAdmin" class="admin-section">
        <span class="admin-section__title">Администрирование</span>
        <RouterLink :to="{ name: 'dashboard' }" class="nav-link">
          Статистика
        </RouterLink>
        <RouterLink :to="{ name: 'admin-managers' }" class="nav-link">
          Менеджеры
        </RouterLink>
        <RouterLink :to="{ name: 'projects' }" class="nav-link">
          Проекты
        </RouterLink>
      </div>

    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  width: 240px;
  height: 100vh;
  background-color: #2c3e50;
  color: #ecf0f1;
  border-right: 1px solid #34495e;
}

.sidebar__logo {
  font-size: 1.5rem;
  font-weight: 700;
  padding: 1.25rem 1.5rem;
  text-align: left;
  color: #ffffff;
  background-color: #34495e;
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  padding: 1rem 0;
}

.nav-link {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  color: #ecf0f1;
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.nav-link:hover {
  background-color: #34495e;
}

.nav-link.router-link-exact-active {
  background-color: #1abc9c;
  color: #ffffff;
  font-weight: 600;
}

.admin-section {
  display: flex;
  flex-direction: column;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #34495e;
}
.admin-section__title {
  margin-bottom: 10px;
  padding: 0 1.5rem 0.5rem;
  font-size: 0.8rem;
  text-transform: uppercase;
  color: #95a5a6;
}
</style>