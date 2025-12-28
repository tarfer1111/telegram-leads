<script lang="ts" setup>
import { RouterLink } from 'vue-router';
</script>

<template>
  <div class="not-found-view">
    <div class="container">
      <h1 class="status-code">404</h1>
      <h2 class="message">Страница не найдена</h2>
      <p class="description">
        Извините, мы не можем найти страницу, которую вы ищете.
      </p>
      <RouterLink :to="{ name: 'dashboard' }" class="home-link">
        Вернуться на Дашборд
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.not-found-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
  text-align: center;
  font-family: Arial, sans-serif;
}

.container {
  padding: 2rem;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.status-code {
  font-size: 6rem;
  font-weight: 700;
  color: #1abc9c;
  margin: 0;
}

.message {
  font-size: 1.8rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0.5rem 0;
}

.description {
  font-size: 1rem;
  color: #555;
  margin-bottom: 2rem;
}

.home-link {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #ffffff;
  background-color: #1abc9c;
  border: none;
  border-radius: 6px;
  text-decoration: none;
  transition: background-color 0.2s;
}

.home-link:hover {
  background-color: #16a085;
}
</style>