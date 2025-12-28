<script lang="ts" setup>
import { useAuthStore } from '@/stores/auth.store';

const authStore = useAuthStore();

const handleLogout = () => {
  if (confirm('Вы уверены, что хотите выйти?')) {
    authStore.logout();
  }
};
</script>

<template>
  <nav class="navbar">
    <div class="navbar__user">
      Привет, **{{ authStore.userFullName }}**
    </div>
    <button @click="handleLogout" class="navbar__logout-btn">
      Выйти
    </button>
  </nav>
</template>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 2rem;
  height: 60px;
  background-color: #ffffff;
  border-bottom: 1px solid #e4e7eb;
}

.navbar__user {
  font-size: 0.9rem;
  color: #333;
}

.navbar__logout-btn {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: #d9534f;
  background-color: transparent;
  border: 1px solid #d9534f;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.navbar__logout-btn:hover {
  background-color: #d9534f;
  color: #ffffff;
}
</style>