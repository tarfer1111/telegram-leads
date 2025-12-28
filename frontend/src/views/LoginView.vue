<script lang="ts" setup>
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth.store';
import type { LoginRequestForm } from '@/types/api.types';

const authStore = useAuthStore();

const username = ref('');
const password = ref('');

const isLoading = ref(false);
const errorMessage = ref<string | null>(null);

const handleSubmit = async () => {
  isLoading.value = true;
  errorMessage.value = null;

  try {
    const loginData: LoginRequestForm = {
      username: username.value,
      password: password.value,
    };

    await authStore.login(loginData);
  } catch (error: any) {
    console.error('Login error in component:', error);
    if (error.response && error.response.status === 401) {
      errorMessage.value = 'Неверный логин или пароль.';
    } else {
      errorMessage.value = 'Произошла ошибка сети. Попробуйте позже.';
    }

  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="login-view">
    <h1 class="login-view__title">Вход в систему</h1>
    <p class="login-view__subtitle">Telegram Leads System</p>

    <form @submit.prevent="handleSubmit" class="login-form">

      <div class="form-group">
        <label for="username">Имя пользователя</label>
        <input
            v-model="username"
            type="text"
            id="username"
            required
            :disabled="isLoading"
        />
      </div>

      <div class="form-group">
        <label for="password">Пароль</label>
        <input
            v-model="password"
            type="password"
            id="password"
            required
            :disabled="isLoading"
        />
      </div>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <button type="submit" class="submit-button" :disabled="isLoading">
        {{ isLoading ? 'Вход...' : 'Войти' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-view {
  width: 100%;
}

.login-view__title {
  font-size: 1.8rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 0.5rem;
}

.login-view__subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 2rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #333;
}

.form-group input {
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #1abc9c;
  box-shadow: 0 0 0 3px rgba(26, 188, 156, 0.2);
}

.submit-button {
  padding: 0.85rem;
  font-size: 1rem;
  font-weight: 600;
  color: #ffffff;
  background-color: #1abc9c;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 1rem;
}

.submit-button:hover:not(:disabled) {
  background-color: #16a085;
}

.submit-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.error-message {
  padding: 0.75rem 1rem;
  background-color: #fbeaea;
  color: #c0392b;
  border: 1px solid #e74c3c;
  border-radius: 6px;
  text-align: center;
  font-size: 0.9rem;
}
</style>