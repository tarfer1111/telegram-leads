<script lang="ts" setup>
import { ref, onMounted, watch } from 'vue';
import {
  getOverviewStats,
  getDailyStats,
  getAllManagerStats,
  get24hManagerStats,
  getDailyManagerStats
} from '@/services/stats.api';
import type {
  OverviewStats,
  DailyStats,
  ManagerStats,
  ManagerStats24h,
  DailyManagerStats,
  GetDailyManagerStatsParams
} from '@/types/api.types';
import { useAuthStore } from '@/stores/auth.store';

const authStore = useAuthStore();

const overviewStats = ref<OverviewStats | null>(null);
const isLoadingOverview = ref(true);
const overviewError = ref<string | null>(null);

// [ИЗМЕНЕНИЕ] Обновлена секция "Статистика по менеджерам"
const managerStatsPeriod = ref<'all' | '24h' | 'custom'>('24h'); // Добавлен 'custom'
const allTimeManagerStats = ref<ManagerStats[]>([]);
const managerStats24h = ref<ManagerStats24h[]>([]);
const dailyManagerStats = ref<DailyManagerStats[]>([]); // Новое хранилище для 'custom'
const isLoadingManagers = ref(true);
const managerError = ref<string | null>(null);

// [ИЗМЕНЕНИЕ] Состояние для календаря
const formatDateForAPI = (date: Date): string => {
  return date.toISOString().split('T')[0];
};
const today = new Date();
const sevenDaysAgo = new Date(Date.now() - 6 * 24 * 60 * 60 * 1000);
const customStartDate = ref(formatDateForAPI(sevenDaysAgo));
const customEndDate = ref(formatDateForAPI(today));


// Эта секция остается без изменений
const dailyStats = ref<DailyStats[]>([]);
const isLoadingDaily = ref(true);
const dailyError = ref<string | null>(null);

const fetchOverview = async () => {
  try {
    isLoadingOverview.value = true;
    overviewStats.value = await getOverviewStats();
  } catch (e: any) {
    console.error('Failed to fetch overview stats:', e);
    overviewError.value = 'Не удалось загрузить общую статистику.';
  } finally {
    isLoadingOverview.value = false;
  }
};

// Эта секция остается без изменений
const fetchDaily = async () => {
  try {
    isLoadingDaily.value = true;
    dailyStats.value = await getDailyStats(7);
  } catch (e: any) {
    console.error('Failed to fetch daily stats:', e);
    dailyError.value = 'Не удалось загрузить статистику по дням.';
  } finally {
    isLoadingDaily.value = false;
  }
};

// [ИЗМЕНЕНИЕ] Функция загрузки менеджеров теперь стала сложнее
const fetchManagers = async () => {
  try {
    isLoadingManagers.value = true;
    managerError.value = null;

    // Очищаем старые данные
    allTimeManagerStats.value = [];
    managerStats24h.value = [];
    dailyManagerStats.value = [];

    if (managerStatsPeriod.value === 'all') {
      allTimeManagerStats.value = await getAllManagerStats();
    }
    else if (managerStatsPeriod.value === '24h') {
      managerStats24h.value = await get24hManagerStats();
    }
    else if (managerStatsPeriod.value === 'custom') {
      if (!customStartDate.value || !customEndDate.value) {
        managerError.value = "Выберите даты";
        return;
      }
      const params: GetDailyManagerStatsParams = {
        start_date: customStartDate.value,
        end_date: customEndDate.value
      };
      dailyManagerStats.value = await getDailyManagerStats(params);
    }

  } catch (e: any) {
    console.error('Failed to fetch manager stats:', e);
    managerError.value = 'Не удалось загрузить статистику по менеджерам.';
  } finally {
    isLoadingManagers.value = false;
  }
};

// [ИЗМЕНЕНИЕ] Следим за сменой 'all' / '24h'. Если 'custom', то ждем нажатия кнопки.
watch(managerStatsPeriod, (newPeriod) => {
  if (newPeriod !== 'custom') {
    fetchManagers();
  }
});


const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

onMounted(() => {
  fetchOverview();
  fetchManagers(); // Загрузит '24h' по умолчанию
  fetchDaily(); // Загрузит "Активность за 7 дней"
});
</script>

<template>
  <div class="dashboard-view">
    <h1 class="page-title">
      Добро пожаловать, {{ authStore.userFullName }}!
    </h1>
    <p class="page-subtitle">Общая статистика по системе</p>

    <div v-if="isLoadingOverview" class="loading-state">
      Загрузка статистики...
    </div>
    <div v-else-if="overviewError" class="error-state">
      {{ overviewError }}
    </div>
    <div v-else-if="overviewStats" class="stats-grid">
      <div class="stat-card">
        <span class="stat-card__label">Всего лидов</span>
        <span class="stat-card__value">{{ overviewStats.total_leads }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-card__label">Активные лиды</span>
        <span class="stat-card__value">{{ overviewStats.active_leads }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-card__label">Закрытые лиды</span>
        <span class="stat-card__value">{{ overviewStats.closed_leads }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-card__label">Всего сообщений</span>
        <span class="stat-card__value">{{ overviewStats.total_messages }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-card__label">Менеджеров</span>
        <span class="stat-card__value">{{ overviewStats.managers_count }}</span>
      </div>
    </div>

    <div class="details-grid">

      <div class="stats-table-container">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
          <h2 class="section-title">Статистика по менеджерам</h2>

          <div class="stats-toggle">
            <button
                :class="{ 'active': managerStatsPeriod === '24h' }"
                @click="managerStatsPeriod = '24h'"
            >
              24h
            </button>
            <button
                :class="{ 'active': managerStatsPeriod === 'all' }"
                @click="managerStatsPeriod = 'all'"
            >
              All
            </button>
            <button
                :class="{ 'active': managerStatsPeriod === 'custom' }"
                @click="managerStatsPeriod = 'custom'"
            >
              Кастом
            </button>
          </div>
        </div>

        <div v-if="managerStatsPeriod === 'custom'" class="custom-date-picker">
          <input type="date" v-model="customStartDate" />
          <span>&mdash;</span>
          <input type="date" v-model="customEndDate" />
          <button @click="fetchManagers" class="apply-btn">Применить</button>
        </div>


        <div v-if="isLoadingManagers" class="loading-state">Загрузка...</div>
        <div v-else-if="managerError" class="error-state">{{ managerError }}</div>

        <div v-else>
          <table v-if="managerStatsPeriod === 'all'" class="stats-table">
            <thead>
            <tr>
              <th>Менеджер</th>
              <th>Всего</th>
              <th>Активные</th>
              <th>Закрытые</th>
              <th>Сообщения</th>
            </tr>
            </thead>
            <tbody>
            <tr v-if="allTimeManagerStats.length === 0">
              <td colspan="5" class="empty-state">Нет данных за все время.</td>
            </tr>
            <tr v-else v-for="stat in allTimeManagerStats" :key="stat.manager_id">
              <td>{{ stat.manager_name }}</td>
              <td>{{ stat.total_leads }}</td>
              <td>{{ stat.active_leads }}</td>
              <td>{{ stat.closed_leads }}</td>
              <td>{{ stat.total_messages }}</td>
            </tr>
            </tbody>
          </table>

          <table v-if="managerStatsPeriod === '24h'" class="stats-table">
            <thead>
            <tr>
              <th>Менеджер</th>
              <th>New</th>
              <th>Закрытые</th>
              <th>Сообщения</th>
            </tr>
            </thead>
            <tbody>
            <tr v-if="managerStats24h.length === 0">
              <td colspan="4" class="empty-state">Нет данных за 24 часа.</td>
            </tr>
            <tr v-else v-for="stat in managerStats24h" :key="stat.manager_id">
              <td>{{ stat.manager_name }}</td>
              <td>{{ stat.new_leads }}</td>
              <td>{{ stat.closed_leads }}</td>
              <td>{{ stat.messages_count }}</td>
            </tr>
            </tbody>
          </table>

          <table v-if="managerStatsPeriod === 'custom'" class="stats-table">
            <thead>
            <tr>
              <th>Дата</th>
              <th>Менеджер</th>
              <th>New</th>
              <th>Закрытые</th>
              <th>Сообщения</th>
            </tr>
            </thead>
            <tbody>
            <tr v-if="dailyManagerStats.length === 0">
              <td colspan="5" class="empty-state">Нет данных за выбранный период.</td>
            </tr>
            <tr v-else v-for="(stat, index) in dailyManagerStats" :key="`${stat.date}-${stat.manager_id}`">
              <td>{{ formatDate(stat.date) }}</td>
              <td>{{ stat.manager_name }}</td>
              <td>{{ stat.new_leads }}</td>
              <td>{{ stat.closed_leads }}</td>
              <td>{{ stat.messages_count }}</td>
            </tr>
            </tbody>
          </table>

        </div>
      </div>

      <div class="stats-table-container">
        <h2 class="section-title">Активность за 7 дней</h2>

        <div v-if="isLoadingDaily" class="loading-state">Загрузка...</div>
        <div v-else-if="dailyError" class="error-state">{{ dailyError }}</div>
        <table v-else class="stats-table">
          <thead>
          <tr>
            <th>Дата</th>
            <th>Новые лиды</th>
            <th>Закрытые</th>
            <th>Сообщения</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="stat in dailyStats" :key="stat.date">
            <td>{{ formatDate(stat.date) }}</td>
            <td>{{ stat.new_leads }}</td>
            <td>{{ stat.closed_leads }}</td>
            <td>{{ stat.messages_count }}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* Все твои старые стили остаются без изменений */
.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}
.page-subtitle {
  font-size: 1rem;
  color: #555;
  margin-bottom: 2rem;
}
.section-title {
  font-size: 1.3rem;
  margin-top: 0;
  font-weight: 600;
  margin-bottom: 1rem;
}

.loading-state,
.error-state {
  font-size: 1.1rem;
  color: #777;
  padding: 2rem;
  text-align: center;
  background-color: #fff;
  border-radius: 8px;
}
.error-state {
  color: #d9534f;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}
.stat-card {
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border-top: 4px solid #1abc9c;
}
.stat-card__label {
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  font-weight: 500;
}
.stat-card__value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  align-items: flex-start;
}
@media (max-width: 1200px) {
  .details-grid {
    grid-template-columns: 1fr;
  }
}

.stats-table-container {
  background-color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.stats-table-container .loading-state,
.stats-table-container .error-state {
  padding: 1rem;
  font-size: 1rem;
  background-color: #f9f9f9;
}

.stats-table {
  width: 100%;
  border-collapse: collapse;
}
.stats-table th,
.stats-table td {
  padding: 0.8rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e4e7eb;
}
.stats-table th {
  font-size: 0.85rem;
  font-weight: 600;
  color: #555;
  background-color: #f8f9fa;
}
.stats-table td {
  font-size: 0.9rem;
}
.stats-table td:not(:first-child),
.stats-table th:not(:first-child) {
  text-align: right;
}
/* [ИЗМЕНЕНИЕ] 👇 Особое правило для новой таблицы (колонки 1 и 2 - по левому краю) */
.stats-table td:nth-child(2),
.stats-table th:nth-child(2) {
  text-align: left;
}


.stats-toggle {
  display: flex;
  background-color: #f0f2f5;
  border-radius: 8px;
  padding: 4px;
  /* max-width: 300px; */ /* [ИЗМЕНЕНИЕ] Убрал, чтобы влезла 3я кнопка */
  margin-bottom: 1rem;
}
.stats-toggle button {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: none;
  background-color: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  color: #555;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  white-space: nowrap; /* [ИЗМЕНЕНИЕ] Добавлено */
}
.stats-toggle button.active {
  background-color: #ffffff;
  color: #1abc9c;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  font-weight: 600;
}

.stats-table td.empty-state {
  text-align: center;
  color: #777;
  font-style: italic;
  padding: 1.5rem;
}

/* [ИЗМЕНЕНИЕ] 👇 Новые стили для календаря */
.custom-date-picker {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem; /* [ИЗМЕНЕНИЕ] Раньше было в другом месте */
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  flex-wrap: wrap; /* [ИЗМЕНЕНИЕ] Для мобилок */
}
.custom-date-picker input[type="date"] {
  padding: 0.4rem 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.9rem;
}
.custom-date-picker .apply-btn {
  padding: 0.5rem 1rem;
  border: none;
  background-color: #1abc9c;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  margin-left: auto; /* [ИЗМЕНЕНИЕ] Кнопка прижата вправо */
}
.custom-date-picker .apply-btn:hover {
  background-color: #16a085;
}
</style>