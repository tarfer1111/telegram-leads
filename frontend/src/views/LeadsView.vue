<script lang="ts" setup>
// [ИЗМЕНЕНИЕ] Добавлены 'watch' и 'useRoute'
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router'; // [ИЗМЕНЕНИЕ]
import { getLeads } from '@/services/leads.api';
import type { LeadResponse, LeadStatus } from '@/services/leads.api';

const router = useRouter();
const route = useRoute(); // [ИЗМЕНЕНИЕ] Получаем доступ к текущему роуту

const allLeads = ref<LeadResponse[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

const statusOptions: { label: string; value: LeadStatus }[] = [
  { label: 'Новые', value: 'new' },
  { label: 'В работе', value: 'in_progress' },
  { label: 'Прочитано', value: 'read' },
  { label: 'Закрытые', value: 'closed' }
];

// [ИЗМЕНЕНИЕ] Функция для безопасного получения статусов из URL
const getStatusesFromQuery = (): LeadStatus[] => {
  const defaultStatuses: LeadStatus[] = ['new', 'in_progress', 'read'];
  const queryStatus = route.query.status;

  if (!queryStatus) return defaultStatuses;

  const validStatuses: Set<LeadStatus> = new Set(statusOptions.map(opt => opt.value));
  const statuses = Array.isArray(queryStatus) ? queryStatus : [queryStatus];

  const filtered = statuses
      .map(s => String(s))
      .filter(s => validStatuses.has(s as LeadStatus)) as LeadStatus[];

  return filtered.length > 0 ? filtered : defaultStatuses;
};

// [ИЗМЕНЕНИЕ] Инициализируем состояние из URL
const selectedStatuses = ref<LeadStatus[]>(getStatusesFromQuery());
const currentPage = ref(parseInt(route.query.page as string, 10) || 1);
const itemsPerPage = 30;

// ... (computed-свойства 'filteredLeads' и 'sortedLeads' остаются без изменений) ...

const filteredLeads = computed(() => {
  return allLeads.value.filter(lead =>
      selectedStatuses.value.includes(lead.status as LeadStatus)
  );
});

const sortedLeads = computed(() => {
  return filteredLeads.value.slice().sort((a, b) => {
    const dateA = new Date(a.last_updated_at).getTime();
    const dateB = new Date(b.last_updated_at).getTime();
    return dateB - dateA;
  });
});

const totalPages = computed(() => {
  return Math.ceil(sortedLeads.value.length / itemsPerPage);
});

// [ИЗМЕНЕНИЕ] Немного изменена логика 'paginatedLeads', чтобы не сбрасывать currentPage
const paginatedLeads = computed(() => {
  // Убедимся, что текущая страница не больше, чем всего страниц
  // (но не сбрасываем ее на 1, если она валидна)
  let page = currentPage.value;
  if (page > totalPages.value && totalPages.value > 0) {
    page = totalPages.value; // Переходим на последнюю доступную страницу
  } else if (page < 1) {
    page = 1;
  }

  const start = (page - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return sortedLeads.value.slice(start, end);
});


const fetchLeads = async () => {
  try {
    isLoading.value = true;
    error.value = null;

    const data = await getLeads('');
    allLeads.value = data;

    // [ИЗМЕНЕНИЕ] ЭТА СТРОКА УДАЛЕНА - она и была главной причиной бага
    // currentPage.value = 1;

    // [ИЗМЕНЕНИЕ] Добавлена проверка: если страница из URL стала невалидной
    // (например, после применения фильтров стало меньше страниц),
    // то корректируем ее.
    if (currentPage.value > totalPages.value) {
      currentPage.value = Math.max(1, totalPages.value);
    }

  } catch (e: any) {
    console.error('Failed to fetch leads:', e);
    error.value = 'Не удалось загрузить список лидов.';
  } finally {
    isLoading.value = false;
  }
};

const handleRefresh = () => {
  // При обновлении можно сбросить на первую страницу,
  // но лучше просто перезагрузить данные.
  // fetchLeads() теперь не сбрасывает страницу.
  fetchLeads();
};

// [ИЗМЕНЕНИЕ] Следим за 'currentPage' и 'selectedStatuses' и обновляем URL
watch([currentPage, selectedStatuses], ([newPage, newStatuses]) => {
  // Сбрасываем страницу на 1, если изменились фильтры
  // (Это нужно делать здесь, а не в computed)
  if (newPage > totalPages.value) {
    currentPage.value = 1; // Сброс, если текущая страница стала невалидной
  }

  router.replace({
    query: {
      // page: currentPage.value > 1 ? currentPage.value : undefined, // не показывать page=1
      page: currentPage.value, // или всегда показывать, так проще
      status: newStatuses
    }
  });
}, {
  deep: true // Нужно для отслеживания изменений внутри массива selectedStatuses
});

// Функции prevPage и nextPage остаются без изменений
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
  }
};
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
  }
};

const goToLeadDetails = (leadId: number) => {
  // Эта функция остается без изменений
  router.push({ name: 'lead-detail', params: { id: leadId } });
};

const formatDate = (dateString: string) => {
  // Эта функция остается без изменений
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('ru-RU');
};

onMounted(fetchLeads);

</script>

<template>
  <div class="leads-view">
    <div class="page-header">
      <h1 class="page-title">Список Лидов</h1>

      <div class="header-actions">
        <div class="filter-group">
          <label>Статус:</label>
          <div class="checkbox-group">
            <div
                v-for="option in statusOptions"
                :key="option.value"
                class="checkbox-item"
            >
              <input
                  type="checkbox"
                  :id="`status-${option.value}`"
                  :value="option.value"
                  v-model="selectedStatuses"
              />
              <label :for="`status-${option.value}`">{{ option.label }}</label>
            </div>
          </div>
        </div>

        <button @click="handleRefresh" class="refresh-btn" :disabled="isLoading">
          {{ isLoading ? 'Загрузка...' : 'Обновить' }}
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="loading-state">
      Загрузка лидов...
    </div>

    <div v-else-if="error" class="error-state">
      {{ error }}
    </div>

    <div v-else-if="paginatedLeads.length === 0" class="no-data-state">
      Лиды с выбранными статусами не найдены.
    </div>

    <div v-else class="table-container">
      <table class="leads-table">
        <thead>
        <tr>
          <th>ID</th>
          <th>Имя/Никнейм (TG)</th>
          <th>Username</th>
          <th>Проект</th>
          <th>Статус</th>
          <th>Менеджер</th>
          <th>Дата создания</th>
          <th>Дата обновления</th>
        </tr>
        </thead>
        <tbody>
        <tr
            v-for="lead in paginatedLeads"
            :key="lead.id"
            @click="goToLeadDetails(lead.id)"
            class="lead-row"
        >
          <td>{{ lead.id }}</td>
          <td>
            {{ lead.telegram_first_name || lead.telegram_username || 'N/A' }}
          </td>
          <td>@{{ lead.telegram_username }}</td>
          <td>{{ lead.project_name }}</td>
          <td>
              <span class="status-badge" :class="`status-${lead.status}`">
                {{ lead.status }}
              </span>
          </td>
          <td>{{ lead.assigned_manager_id }}</td>
          <td>{{ formatDate(lead.created_at) }}</td>
          <td>{{ formatDate(lead.last_updated_at) }}</td>
        </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!isLoading && totalPages > 1" class="pagination-controls">
      <button @click="prevPage" :disabled="currentPage === 1">
        &laquo; Назад
      </button>
      <span>
        Страница {{ currentPage }} из {{ totalPages }}
        (Всего: {{ sortedLeads.length }})
      </span>
      <button @click="nextPage" :disabled="currentPage === totalPages">
        Вперед &raquo;
      </button>
    </div>

  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.filter-group label {
  font-weight: 500;
  white-space: nowrap;
}

.refresh-btn {
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: #fff;
  background-color: #3498db;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  height: fit-content;
}
.refresh-btn:hover {
  background-color: #2980b9;
}
.refresh-btn:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.checkbox-group {
  display: flex;
  gap: 1rem;
}
.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.checkbox-item label {
  font-size: 0.9rem;
  font-weight: 400;
  cursor: pointer;
}
.checkbox-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.loading-state,
.error-state,
.no-data-state {
  font-size: 1.2rem;
  color: #777;
  padding: 2rem;
  text-align: center;
  background-color: #fff;
  border-radius: 8px;
}
.error-state { color: #d9534f; }

.table-container {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.leads-table {
  width: 100%;
  border-collapse: collapse;
}

.leads-table th,
.leads-table td {
  padding: 1rem 1.25rem;
  text-align: left;
  border-bottom: 1px solid #e4e7eb;
}

.leads-table th {
  background-color: #f8f9fa;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #555;
}

.leads-table td {
  font-size: 0.95rem;
}

.lead-row {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.lead-row:hover {
  background-color: #f9f9f9;
}

.status-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: capitalize;
  color: #fff;
}
.status-new { background-color: #3498db; }
.status-in_progress { background-color: #f39c12; }
.status-closed { background-color: #95a5a6; }
.status-read { background-color: #6f0080; }

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.pagination-controls span {
  font-size: 0.9rem;
  font-weight: 500;
  color: #555;
}
.pagination-controls button {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  background-color: #ecf0f1;
  border: 1px solid #bdc3c7;
  border-radius: 6px;
  cursor: pointer;
}
.pagination-controls button:disabled {
  background-color: #f9f9f9;
  color: #bdc3c7;
  cursor: not-allowed;
}
</style>