<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { getProjects, createProject, deleteProject } from '@/services/projects.api';
import type { ProjectResponse, ProjectCreate } from '@/types/api.types';

const projects = ref<ProjectResponse[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

const newProjectName = ref('');
const isCreating = ref(false);
const createError = ref<string | null>(null);

const fetchProjects = async () => {
  try {
    isLoading.value = true;
    error.value = null;
    projects.value = await getProjects();
  } catch (e: any) {
    console.error('Failed to fetch projects:', e);
    error.value = 'Не удалось загрузить проекты.';
  } finally {
    isLoading.value = false;
  }
};

const handleCreateProject = async () => {
  if (!newProjectName.value.trim()) {
    createError.value = 'Название проекта не может быть пустым.';
    return;
  }

  try {
    isCreating.value = true;
    createError.value = null;

    const projectData: ProjectCreate = {
      name: newProjectName.value.trim()
    };

    const newProject = await createProject(projectData);
    projects.value.push(newProject);
    newProjectName.value = '';

  } catch (e: any) {
    console.error('Failed to create project:', e);
    createError.value = 'Ошибка при создании проекта.';
  } finally {
    isCreating.value = false;
  }
};

const handleDeleteProject = async (projectId: number) => {
  if (!confirm(`Вы уверены, что хотите удалить проект ID: ${projectId}? Это действие необратимо.`)) {
    return;
  }

  try {
    await deleteProject(projectId);
    projects.value = projects.value.filter(p => p.id !== projectId);
  } catch (e: any) {
    console.error('Failed to delete project:', e);
    alert('Ошибка при удалении проекта.');
  }
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('ru-RU');
};

onMounted(fetchProjects);
</script>

<template>
  <div class="projects-view">
    <h1 class="page-title">Управление Проектами</h1>

    <form @submit.prevent="handleCreateProject" class="create-project-form">
      <h3>Создать новый проект</h3>
      <div class="form-row">
        <input
            v-model="newProjectName"
            type="text"
            placeholder="Название нового проекта"
            :disabled="isCreating"
        />
        <button type="submit" :disabled="isCreating">
          {{ isCreating ? '...' : 'Создать' }}
        </button>
      </div>
      <div v-if="createError" class="error-message">
        {{ createError }}
      </div>
    </form>

    <div class="projects-list-container">
      <h3>Существующие проекты</h3>

      <div v-if="isLoading" class="loading-state">Загрузка проектов...</div>
      <div v-else-if="error" class="error-state">{{ error }}</div>
      <div v-else-if="projects.length === 0" class="no-data-state">
        Проектов пока нет.
      </div>

      <table v-else class="projects-table">
        <thead>
        <tr>
          <th>ID</th>
          <th>Название</th>
          <th>Дата создания</th>
          <th>Действия</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="project in projects" :key="project.id">
          <td>{{ project.id }}</td>
          <td>{{ project.name }}</td>
          <td>{{ formatDate(project.created_at) }}</td>
          <td>
            <RouterLink
                :to="{ name: 'project-detail', params: { id: project.id } }"
                class="action-btn manage-btn"
            >
              Управлять
            </RouterLink>
            <button
                @click="handleDeleteProject(project.id)"
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
.create-project-form {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 2rem;
}
.create-project-form h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}
.form-row {
  display: flex;
  gap: 1rem;
}
.form-row input {
  flex-grow: 1;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 6px;
}
.form-row button {
  padding: 0 1.5rem;
  font-weight: 600;
  color: #fff;
  background-color: #1abc9c;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.form-row button:disabled {
  background-color: #95a5a6;
}
.error-message {
  color: #d9534f;
  font-size: 0.9rem;
  margin-top: 0.75rem;
}

.projects-list-container {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.projects-list-container h3 {
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

.projects-table {
  width: 100%;
  border-collapse: collapse;
}
.projects-table th,
.projects-table td {
  padding: 0.8rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e4e7eb;
}
.projects-table th {
  background-color: #f8f9fa;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
}

.action-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  font-weight: 500;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin-right: 0.5rem;
}

.manage-btn {
  background-color: #3498db;
  color: #fff;
  text-decoration: none;
  display: inline-block;
  line-height: 1.4;
}
.manage-btn:hover {
  background-color: #2980b9;
}

.delete-btn {
  background-color: #e74c3c;
  color: #fff;
}
.delete-btn:hover {
  background-color: #c0392b;
}
</style>