<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import {
  getProjectDetails,
  getProjectBots,
  createBot,
  deleteBot,
  addManagersToProject,
  removeManagerFromProject,
  updateProject,
  updateBot
} from '@/services/projects.api';
import type {
  ProjectWithManagersResponse,
  BotResponse,
  BotCreate,
  BotUpdate,
  UserResponse,
  ProjectCreate
} from '@/types/api.types';

// --- Props & Router ---
const props = defineProps<{
  id: string; // из URL
}>();

const projectId = parseInt(props.id, 10);

const project = ref<ProjectWithManagersResponse | null>(null);
const bots = ref<BotResponse[]>([]);
const isLoadingProject = ref(true);
const isLoadingBots = ref(true);
const error = ref<string | null>(null);

const createForm = reactive<BotCreate>({
  identifier: '',
  name: '',
  token: '',
  auto_reply: 'Спасибо за ваше сообщение!'
});
const isCreating = ref(false);
const createError = ref<string | null>(null);

const addManagerId = ref('');
const isAddingManager = ref(false);
const addManagerError = ref<string | null>(null);

const isEditProjectModalVisible = ref(false);
const isUpdatingProject = ref(false);
const editProjectForm = reactive<ProjectCreate>({ name: '' });

const openEditProjectModal = () => {
  if (!project.value) return;
  editProjectForm.name = project.value.name;
  isEditProjectModalVisible.value = true;
};
const closeEditProjectModal = () => {
  isEditProjectModalVisible.value = false;
};

const isEditBotModalVisible = ref(false);
const isUpdatingBot = ref(false);
const selectedBot = ref<BotResponse | null>(null);
const editBotForm = reactive<BotUpdate>({
  name: '',
  identifier: '',
  token: '',
  auto_reply: '',
  is_active: true
});

const openEditBotModal = (bot: BotResponse) => {
  selectedBot.value = bot;

  editBotForm.name = bot.name;
  editBotForm.identifier = bot.identifier;
  editBotForm.auto_reply = bot.auto_reply;
  editBotForm.is_active = bot.is_active;
  editBotForm.token = '';

  isEditBotModalVisible.value = true;
};
const closeEditBotModal = () => {
  isEditBotModalVisible.value = false;
  selectedBot.value = null; // Сбрасываем выбранного бота
};

const fetchProjectData = async () => {
  try {
    isLoadingProject.value = true;
    error.value = null;
    project.value = await getProjectDetails(projectId);
  } catch (e: any) {
    console.error('Failed to fetch project details:', e);
    error.value = 'Не удалось загрузить данные проекта.';
  } finally {
    isLoadingProject.value = false;
  }
};

const fetchBots = async () => {
  try {
    isLoadingBots.value = true;
    bots.value = await getProjectBots(projectId);
  } catch (e: any) {
    console.error('Failed to fetch bots:', e);
    if (!error.value) {
      error.value = 'Не удалось загрузить список ботов.';
    }
  } finally {
    isLoadingBots.value = false;
  }
};

const handleUpdateProject = async () => {
  if (!editProjectForm.name) return;
  try {
    isUpdatingProject.value = true;
    const updatedProject = await updateProject(projectId, editProjectForm);

    if (project.value) {
      project.value.name = updatedProject.name;
    }
    closeEditProjectModal();
  } catch (e: any) {
    console.error('Failed to update project:', e);
    alert('Ошибка при обновлении проекта.');
  } finally {
    isUpdatingProject.value = false;
  }
};

const handleAddManager = async () => {
  const parsedId = parseInt(addManagerId.value, 10);
  if (isNaN(parsedId) || parsedId <= 0) {
    addManagerError.value = 'Введите корректный ID пользователя.';
    return;
  }

  try {
    isAddingManager.value = true;
    addManagerError.value = null;
    await addManagersToProject(projectId, { manager_ids: [parsedId] });
    addManagerId.value = '';
    await fetchProjectData();
  } catch (e: any) {
    console.error('Failed to add manager:', e);
    addManagerError.value = 'Ошибка при добавлении менеджера. ' + (e.response?.data?.detail || e.message);
  } finally {
    isAddingManager.value = false;
  }
};

const handleRemoveManager = async (manager: UserResponse) => {
  const managerName = manager.full_name || manager.username || `ID: ${manager.id}`;
  if (!confirm(`Вы уверены, что хотите удалить менеджера "${managerName}" из проекта?`)) {
    return;
  }
  try {
    await removeManagerFromProject(projectId, manager.id);
    await fetchProjectData(); // Обновляем список
  } catch (e: any) {
    console.error('Failed to remove manager:', e);
    alert('Ошибка при удалении менеджера.');
  }
};

const handleCreateBot = async () => {
  if (!createForm.identifier || !createForm.name || !createForm.token) {
    createError.value = 'Идентификатор, Имя и Токен обязательны.';
    return;
  }

  try {
    isCreating.value = true;
    createError.value = null;
    const newBot = await createBot(projectId, createForm);
    bots.value.push(newBot);

    createForm.identifier = '';
    createForm.name = '';
    createForm.token = '';
    createForm.auto_reply = 'Спасибо за ваше сообщение!';
  } catch (e: any) {
    console.error('Failed to create bot:', e);
    createError.value = 'Ошибка при создании бота. ' + (e.response?.data?.detail || e.message);
  } finally {
    isCreating.value = false;
  }
};

const handleUpdateBot = async () => {
  if (!selectedBot.value) return;

  const payload: BotUpdate = {
    ...editBotForm,
    token: editBotForm.token ? editBotForm.token : null
  };

  try {
    isUpdatingBot.value = true;
    const updatedBot = await updateBot(projectId, selectedBot.value.id, payload);

    const index = bots.value.findIndex(b => b.id === updatedBot.id);
    if (index !== -1) {
      bots.value[index] = updatedBot;
    }

    closeEditBotModal();
  } catch (e: any) {
    console.error('Failed to update bot:', e);
    alert('Ошибка при обновлении бота.');
  } finally {
    isUpdatingBot.value = false;
  }
};

const handleDeleteBot = async (bot: BotResponse) => {
  if (!confirm(`Вы уверены, что хотите удалить бота "${bot.name}" (ID: ${bot.id})?`)) {
    return;
  }
  try {
    await deleteBot(projectId, bot.id);
    bots.value = bots.value.filter(b => b.id !== bot.id);
  } catch (e: any) {
    console.error('Failed to delete bot:', e);
    alert('Ошибка при удалении бота.');
  }
};

onMounted(() => {
  fetchProjectData();
  fetchBots();
});
</script>

<template>
  <div class="project-detail-view">

    <div v-if="isLoadingProject" class="loading-state">Загрузка проекта...</div>
    <div v-else-if="project" class="project-header">
      <div> <h1 class="page-title">
        Проект: {{ project.name }}
      </h1>
        <p class="project-id">ID Проекта: {{ project.id }}</p>
      </div>
      <button @click="openEditProjectModal" class="action-btn edit-btn">
        Редактировать проект
      </button>
    </div>
    <div v-else-if="error" class="error-state">{{ error }}</div>


    <div v-if="project" class="managers-section">

      <form @submit.prevent="handleAddManager" class="add-manager-form">
        <h3>Добавить менеджера</h3>
        <div class="form-group">
          <label>ID Пользователя</label>
          <input v-model="addManagerId" type="text" placeholder="Введите ID..." :disabled="isAddingManager" />
        </div>
        <button type="submit" :disabled="isAddingManager" class="create-button">
          {{ isAddingManager ? '...' : 'Добавить' }}
        </button>
        <div v-if="addManagerError" class="error-message">{{ addManagerError }}</div>
      </form>

      <div class="managers-list-container">
        <h3>Менеджеры проекта</h3>
        <div v-if="!project.managers || project.managers.length === 0" class="no-data-state">
          В проекте нет менеджеров.
        </div>
        <table v-else class="managers-table">
          <thead>
          <tr>
            <th>ID</th>
            <th>Email / Логин</th>
            <th>Действия</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="manager in project.managers" :key="manager.id">
            <td>{{ manager.id }}</td>
            <td>{{ (manager as any).email || manager.username || 'N/A' }}</td>
            <td>
              <button class="action-btn delete-btn" @click="handleRemoveManager(manager)">
                Удалить
              </button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>


    <div v-if="project" class="bots-section">

      <form @submit.prevent="handleCreateBot" class="create-bot-form">
        <h3>Добавить нового бота</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>Имя (в админке)</label>
            <input v-model="createForm.name" type="text" :disabled="isCreating" />
          </div>
          <div class="form-group">
            <label>Идентификатор (ID бота)</label>
            <input v-model="createForm.identifier" type="text" :disabled="isCreating" />
          </div>
          <div class="form-group">
            <label>Токен (Bot Token)</label>
            <input v-model="createForm.token" type="password" :disabled="isCreating" />
          </div>
          <div class="form-group span-3">
            <label>Автоответ (на первое сообщение)</label>
            <input v-model="createForm.auto_reply" type="text" :disabled="isCreating" />
          </div>
          <button type-="submit" :disabled="isCreating" class="create-button">
            {{ isCreating ? '...' : 'Добавить бота' }}
          </button>
        </div>
        <div v-if="createError" class="error-message">{{ createError }}</div>
      </form>

      <div class="bots-list-container">
        <h3>Список ботов проекта</h3>

        <div v-if="isLoadingBots" class="loading-state">Загрузка ботов...</div>
        <div v-else-if="bots.length === 0" class="no-data-state">
          У этого проекта еще нет ботов.
        </div>

        <table v-else class="bots-table">
          <thead>
          <tr>
            <th>ID</th>
            <th>Имя</th>
            <th>Идентификатор</th>
            <th>Webhook URL</th>
            <th>Статус</th>
            <th>Действия</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="bot in bots" :key="bot.id">
            <td>{{ bot.id }}</td>
            <td>{{ bot.name }}</td>
            <td>{{ bot.identifier }}</td>
            <td>{{ bot.webhook_url || 'Не установлен' }}</td>
            <td>
              <span
                  class="status-badge"
                  :class="bot.is_active ? 'status-active' : 'status-inactive'"
              >
                {{ bot.is_active ? 'Активен' : 'Выключен' }}
              </span>
            </td>
            <td class="actions-cell">
              <button class="action-btn edit-btn" @click="openEditBotModal(bot)">
                Ред.
              </button>
              <button class="action-btn delete-btn" @click="handleDeleteBot(bot)">
                Удалить
              </button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>


    <div v-if="isEditProjectModalVisible" class="modal-overlay" @click.self="closeEditProjectModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Редактировать проект</h3>
          <button class="modal-close" @click="closeEditProjectModal">&times;</button>
        </div>
        <form @submit.prevent="handleUpdateProject" class="modal-body">
          <div class="form-group">
            <label>Название проекта</label>
            <input v-model="editProjectForm.name" type="text" :disabled="isUpdatingProject" />
          </div>
          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="closeEditProjectModal">
              Отмена
            </button>
            <button type="submit" class="btn-primary" :disabled="isUpdatingProject">
              {{ isUpdatingProject ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="isEditBotModalVisible && selectedBot" class="modal-overlay" @click.self="closeEditBotModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Редактировать бота: {{ selectedBot.name }}</h3>
          <button class="modal-close" @click="closeEditBotModal">&times;</button>
        </div>
        <form @submit.prevent="handleUpdateBot" class="modal-body">

          <div class="form-group">
            <label>Имя (в админке)</label>
            <input v-model="editBotForm.name" type="text" :disabled="isUpdatingBot" />
          </div>
          <div class="form-group">
            <label>Идентификатор (ID бота)</label>
            <input v-model="editBotForm.identifier" type="text" :disabled="isUpdatingBot" />
          </div>
          <div class="form-group">
            <label>Токен (Bot Token)</label>
            <input v-model="editBotForm.token" type="password" :disabled="isUpdatingBot" placeholder="Оставьте пустым, чтобы не менять" />
          </div>
          <div class="form-group">
            <label>Автоответ (на первое сообщение)</label>
            <input v-model="editBotForm.auto_reply" type="text" :disabled="isUpdatingBot" />
          </div>
          <div class="form-group checkbox-group">
            <input v-model="editBotForm.is_active" type="checkbox" :id="`bot-active-${selectedBot.id}`" :disabled="isUpdatingBot" />
            <label :for="`bot-active-${selectedBot.id}`">Бот Активен</label>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="closeEditBotModal">
              Отмена
            </button>
            <button type="submit" class="btn-primary" :disabled="isUpdatingBot">
              {{ isUpdatingBot ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<style scoped>
.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}
.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}
.project-id {
  font-size: 0.9rem;
  color: #777;
  margin-top: 0;
}

.managers-section, .bots-section {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
  align-items: flex-start;
}
@media (max-width: 1200px) {
  .managers-section, .bots-section {
    grid-template-columns: 1fr;
  }
}

.add-manager-form {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 1.5rem;
}
.add-manager-form h3 { margin-top: 0; margin-bottom: 1.5rem; }
.add-manager-form .form-group { margin-bottom: 1rem; }
.add-manager-form .create-button { width: 100%; padding: 0.75rem 1.5rem; }
.add-manager-form .error-message { grid-column: 1 / -1; }

/* --- Список менеджеров --- */
.managers-list-container {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.managers-list-container h3 { margin-top: 0; margin-bottom: 1rem; }
.managers-table { width: 100%; border-collapse: collapse; }
.managers-table th, .managers-table td {
  padding: 0.8rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e4e7eb;
  vertical-align: middle;
}

.create-bot-form {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom:0rem;
  grid-column: 1 / -1;
}
.create-bot-form h3 { margin-top: 0; margin-bottom: 1.5rem; }
.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem 1rem;
  align-items: flex-end;
}
.form-group { display: flex; flex-direction: column; }
.form-group.span-3 { grid-column: 1 / -1; }
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
  justify-self: end;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  color: #fff;
  background-color: #1abc9c;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  height: fit-content;
}
.form-grid .create-button { grid-column: 3 / 4; }
.create-button:disabled { background-color: #95a5a6; }
.error-message { color: #d9534f; font-size: 0.9rem; margin-top: 1rem; }

.bots-list-container {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  grid-column: 1 / -1;
}
.bots-list-container h3 { margin-top: 0; margin-bottom: 1rem; }

.loading-state, .error-state, .no-data-state {
  font-size: 1.1rem;
  color: #777;
  padding: 2rem;
  text-align: center;
}
.error-state { color: #d9534f; }

.bots-table { width: 100%; border-collapse: collapse; }
.bots-table th, .bots-table td {
  padding: 0.8rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e4e7eb;
  vertical-align: middle;
}
.bots-table td { font-size: 0.9rem; }
.bots-table .actions-cell { width: 120px; }

.status-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
}
.status-active { background-color: #27ae60; }
.status-inactive { background-color: #95a5a6; }

.action-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  font-weight: 500;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin-right: 0.5rem;
}
.action-btn:last-child { margin-right: 0; }
.delete-btn { background-color: #e74c3c; color: #fff; }
.delete-btn:hover { background-color: #c0392b; }
.edit-btn { background-color: #3498db; color: #fff; }
.edit-btn:hover { background-color: #2980b9; }
.project-header .edit-btn { padding: 0.6rem 1rem; font-size: 0.9rem; }

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  z-index: 100;
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal-content {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 500px;
  z-index: 101;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7eb;
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}
.modal-header h3 {
  margin: 0;
  font-size: 1.3rem;
}
.modal-close {
  background: none;
  border: none;
  font-size: 2rem;
  font-weight: 300;
  line-height: 1;
  color: #777;
  cursor: pointer;
}
.modal-body .form-group {
  margin-bottom: 1rem;
}
.modal-body .form-group input[type="password"] {
  font-family: monospace;
}
.modal-body .checkbox-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
}
.modal-body .checkbox-group input {
  width: 16px;
  height: 16px;
}
.modal-body .checkbox-group label {
  margin-bottom: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  border-top: 1px solid #e4e7eb;
  padding-top: 1.5rem;
  margin-top: 2rem;
}
.modal-footer .btn-secondary,
.modal-footer .btn-primary {
  padding: 0.6rem 1.2rem;
  font-size: 0.9rem;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.modal-footer .btn-secondary {
  background-color: #ecf0f1;
  color: #333;
}
.modal-footer .btn-secondary:hover {
  background-color: #bdc3c7;
}
.modal-footer .btn-primary {
  background-color: #1abc9c;
  color: #fff;
}
.modal-footer .btn-primary:disabled {
  background-color: #95a5a6;
}
.actions-cell {
  display: flex;
}
</style>