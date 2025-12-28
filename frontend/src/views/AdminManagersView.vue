<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue';
import {
  getManagers,
  createManager,
  deleteManager,
  updateManager
} from '@/services/managers.api';
import type { ManagerResponse, ManagerCreate, ManagerUpdate } from '@/types/api.types';
import { useAuthStore } from '@/stores/auth.store';

const authStore = useAuthStore();

const managers = ref<ManagerResponse[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

const createForm = reactive<ManagerCreate>({
  username: '',
  password: '',
  full_name: ''
});
const isCreating = ref(false);
const createError = ref<string | null>(null);


/**
 * Загрузка списка менеджеров
 */
const fetchManagers = async () => {
  try {
    isLoading.value = true;
    error.value = null;
    const allManagers = await getManagers();
    managers.value = allManagers.filter(m => m.id !== authStore.user?.id);

  } catch (e: any) {
    console.error('Failed to fetch managers:', e);
    error.value = 'Не удалось загрузить список менеджеров.';
  } finally {
    isLoading.value = false;
  }
};

const handleCreateManager = async () => {
  if (!createForm.username || !createForm.password || !createForm.full_name) {
    createError.value = 'Все поля обязательны для заполнения.';
    return;
  }

  try {
    isCreating.value = true;
    createError.value = null;

    const newManager = await createManager(createForm);

    managers.value.push(newManager);

    createForm.username = '';
    createForm.password = '';
    createForm.full_name = '';

  } catch (e: any) {
    console.error('Failed to create manager:', e);
    createError.value = 'Ошибка при создании: ' + (e.response?.data?.detail || e.message);
  } finally {
    isCreating.value = false;
  }
};

const handleDeleteManager = async (managerId: number) => {
  const manager = managers.value.find(m => m.id === managerId);
  if (!manager) return;

  if (!confirm(`Вы уверены, что хотите удалить менеджера: ${manager.full_name}?`)) {
    return;
  }

  try {
    await deleteManager(managerId);
    managers.value = managers.value.filter(m => m.id !== managerId);
  } catch (e: any) {
    console.error('Failed to delete manager:', e);
    alert('Ошибка при удалении менеджера.');
  }
};

const handleToggleActive = async (manager: ManagerResponse) => {
  const newStatus = !manager.is_active;
  const updateData: ManagerUpdate = { is_active: newStatus };

  try {
    const updatedManager = await updateManager(manager.id, updateData);
    manager.is_active = updatedManager.is_active;
  } catch (e) {
    console.error('Failed to update manager status:', e);
    alert('Ошибка при обновлении статуса.');
  }
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('ru-RU');
};

onMounted(fetchManagers);
</script>

<template>
  <div class="managers-view">
    <h1 class="page-title">Управление Менеджерами</h1>

    <form @submit.prevent="handleCreateManager" class="create-manager-form">
      <h3>Создать нового менеджера</h3>
      <div class="form-grid">
        <div class="form-group">
          <label>Имя пользователя (логин)</label>
          <input v-model="createForm.username" type="text" :disabled="isCreating" />
        </div>
        <div class="form-group">
          <label>Пароль</label>
          <input v-model="createForm.password" type="password" :disabled="isCreating" />
        </div>
        <div class="form-group">
          <label>Полное имя</label>
          <input v-model="createForm.full_name" type="text" :disabled="isCreating" />
        </div>
        <button type="submit" :disabled="isCreating" class="create-button">
          {{ isCreating ? '...' : 'Создать' }}
        </button>
      </div>
      <div v-if="createError" class="error-message">
        {{ createError }}
      </div>
    </form>

    <div class="list-container">
      <h3>Список менеджеров</h3>

      <div v-if="isLoading" class="loading-state">Загрузка...</div>
      <div v-else-if="error" class="error-state">{{ error }}</div>
      <div v-else-if="managers.length === 0" class="no-data-state">
        Других менеджеров пока нет.
      </div>

      <table v-else class="managers-table">
        <thead>
        <tr>
          <th>ID</th>
          <th>Полное имя</th>
          <th>Логин</th>
          <th>Роль</th>
          <th>Статус</th>
          <th>Действия</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="manager in managers" :key="manager.id">
          <td>{{ manager.id }}</td>
          <td>{{ manager.full_name }}</td>
          <td>{{ manager.username }}</td>
          <td>{{ manager.role }}</td>
          <td>
              <span
                  class="status-badge"
                  :class="manager.is_active ? 'status-active' : 'status-inactive'"
              >
                {{ manager.is_active ? 'Активен' : 'Неактивен' }}
              </span>
          </td>
          <td>
            <button
                @click="handleToggleActive(manager)"
                class="action-btn toggle-btn"
                :title="manager.is_active ? 'Деактивировать' : 'Активировать'"
            >
              {{ manager.is_active ? 'Выкл' : 'Вкл' }}
            </button>
            <button
                @click="handleDeleteManager(manager.id)"
                class="action-btn delete-btn"
            >
              Удалить
            </button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>

<style scoped>
.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 2rem;
}

/* Форма создания */
.create-manager-form {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 2rem;
}
.create-manager-form h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr auto;
  gap: 1rem;
  align-items: flex-end;
}
.form-group {
  display: flex;
  flex-direction: column;
}
.form-group label {
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}
.form-group input {
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 6px;
}
.create-button {
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  color: #fff;
  background-color: #1abc9c;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  height: fit-content;
}
.create-button:disabled {
  background-color: #95a5a6;
}
.error-message {
  color: #d9534f;
  font-size: 0.9rem;
  margin-top: 1rem;
}

.list-container {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.list-container h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}

.loading-state, .error-state, .no-data-state {
  font-size: 1.1rem;
  color: #777;
  padding: 2rem;
  text-align: center;
}
.error-state { color: #d9534f; }

/* Таблица */
.managers-table {
  width: 100%;
  border-collapse: collapse;
}
.managers-table th,
.managers-table td {
  padding: 0.8rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e4e7eb;
}

/* Статус */
.status-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
}
.status-active { background-color: #27ae60; }
.status-inactive { background-color: #95a5a6; }

/* Кнопки */
.action-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  font-weight: 500;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin-right: 0.5rem;
}
.toggle-btn {
  background-color: #f39c12;
  color: #fff;
}
.delete-btn {
  background-color: #e74c3c;
  color: #fff;
}
</style>