<script lang="ts" setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  getLeadDetails,
  getMessages,
  sendMessage,
  closeLead,
  markLeadAsRead
} from '@/services/leads.api';
import type { LeadResponse, MessageResponse, SendMessageRequest } from '@/types/api.types';
import { useAuthStore } from '@/stores/auth.store';

const props = defineProps<{
  id: string;
}>();

const router = useRouter();
const authStore = useAuthStore();
const leadId = parseInt(props.id, 10);

const lead = ref<LeadResponse | null>(null);
const messages = ref<MessageResponse[]>([]);
const newMessageText = ref('');

const isLeadLoading = ref(true);
const isMessagesLoading = ref(true);
const isSending = ref(false);
const isMarkingRead = ref(false);
const error = ref<string | null>(null);

const chatMessagesRef = ref<HTMLElement | null>(null);
let pollingInterval: number | undefined;

const fetchLeadData = async () => {
  try {
    isLeadLoading.value = true;
    lead.value = await getLeadDetails(leadId);
  } catch (e) {
    console.error('Failed to fetch lead details:', e);
    error.value = 'Не удалось загрузить данные лида.';
  } finally {
    isLeadLoading.value = false;
  }
};

const fetchMessages = async (isPolling = false) => {
  let success = false;
  if (!isPolling) {
    isMessagesLoading.value = true;
  }

  try {
    const data = await getMessages(leadId);
    messages.value = data;
    success = true;
  } catch (e) {
    console.error('Failed to fetch messages:', e);
    if (!isPolling) {
      error.value = 'Не удалось загрузить сообщения.';
    }
  } finally {
    if (!isPolling) {
      isMessagesLoading.value = false;
    }

    if (success) {
      scrollToBottom();
    }
  }
};

const handleMarkRead = async () => {
  if (isMarkingRead.value) return;

  try {
    isMarkingRead.value = true;
    await markLeadAsRead(leadId);
    await fetchLeadData();
  } catch (e) {
    console.error('Failed to mark lead as read:', e);
    alert('Ошибка при отметке лида как прочитанного.');
  } finally {
    isMarkingRead.value = false;
  }
};

const handleSendMessage = async () => {
  if (!newMessageText.value.trim()) return;

  const messageData: SendMessageRequest = {
    text: newMessageText.value.trim()
  };

  try {
    isSending.value = true;
    await sendMessage(leadId, messageData);
    newMessageText.value = '';
    await fetchMessages(true);
  } catch (e) {
    console.error('Failed to send message:', e);
    alert('Ошибка отправки сообщения.');
  } finally {
    isSending.value = false;
  }
};

const handleCloseLead = async () => {
  if (confirm(`Вы уверены, что хотите закрыть лида ID: ${leadId}?`)) {
    try {
      await closeLead(leadId);
      alert('Лид успешно закрыт.');
      router.push({ name: 'leads' });
    } catch (e) {
      console.error('Failed to close lead:', e);
      alert('Ошибка при закрытии лида.');
    }
  }
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

const scrollToBottom = async () => {
  await nextTick();
  const el = chatMessagesRef.value;
  if (el) {
    el.scrollTop = el.scrollHeight;
  }
};

onMounted(() => {
  fetchLeadData();
  fetchMessages();
  pollingInterval = window.setInterval(() => {
    console.log('Polling for new messages...');
    fetchMessages(true);
  }, 5000);
});

onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }
});
</script>

<template>
  <div class="chat-view">

    <div class="chat-header">
      <button @click="router.back()" class="back-btn">
        &laquo; Назад к списку
      </button>

      <div v-if="isLeadLoading">Загрузка данных лида...</div>
      <div v-else-if="lead" class="chat-header__info">
        <h1 class="chat-header__name">
          Чат: {{ lead.telegram_first_name || lead.telegram_username || `Lead #${lead.id}` }}
        </h1>
        <div class="chat-header__meta">
          <span>Проект: <strong>{{ lead.project_name }}</strong></span>
          <span>|</span>
          <span>Статус: <strong :class="`status-${lead.status}`">{{ lead.status }}</strong></span>
        </div>
      </div>

      <div class="chat-header__actions">
        <button
            v-if="lead && lead.status === 'new'"
            @click="handleMarkRead"
            class="mark-read-btn"
            :disabled="isMarkingRead"
        >
          {{ isMarkingRead ? '...' : 'Прочитано' }}
        </button>

        <button
            v-if="lead && lead.status !== 'closed'"
            @click="handleCloseLead"
            class="close-lead-btn"
        >
          Закрыть лида
        </button>
      </div>
    </div>

    <div class="chat-messages" ref="chatMessagesRef">
      <div v-if="isMessagesLoading" class="loading-state">
        Загрузка сообщений...
      </div>
      <div v-else-if="error" class="error-state">
        {{ error }}
      </div>
      <div v-else-if="messages.length === 0" class="no-data-state">
        Сообщений пока нет.
      </div>

      <div v-else class="message-list">

        <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-row"
            :class="{ 'is-manager-row': msg.sender === 'manager' }"
        >
          <div
              class="message-bubble"
              :class="{ 'is-manager-bubble': msg.sender === 'manager' }"
          >
            <div class="message-bubble__text">{{ msg.text }}</div>

            <div class="message-bubble__meta">
              {{ formatDate(msg.created_at) }}
            </div>
          </div>
        </div>

      </div>
    </div>

    <form v-if="lead && lead.status !== 'closed'" @submit.prevent="handleSendMessage" class="chat-input-form">
      <textarea
          v-model="newMessageText"
          placeholder="Написать сообщение..."
          class="chat-input"
          :disabled="isSending"
          @keydown.enter.prevent="handleSendMessage"
      ></textarea>
      <button type="submit" class="send-button" :disabled="isSending">
        {{ isSending ? '...' : 'Отправить' }}
      </button>
    </form>

    <div v-else class="chat-closed-notice">
      Этот лид закрыт. Общение невозможно.
    </div>

  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 4rem - 60px);
  max-height: 800px;
  max-width: 800px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e4e7eb;
  /* [ИЗМЕНЕНИЕ] 👇 Добавлен gap для отступа кнопки */
  gap: 1rem;
}

/* [ИЗМЕНЕНИЕ] 👇 Добавлены стили для кнопки "Назад" */
.back-btn {
  padding: 0.5rem 1rem;
  font-weight: 500;
  color: #333;
  background-color: #ecf0f1;
  border: 1px solid #bdc3c7;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.2s;
}
.back-btn:hover {
  background-color: #dfe6e9;
}

.chat-header__info {
  flex-grow: 1;
  /* [ИЗМЕНЕНИЕ] 👇 Предотвращает "сжатие" info */
  min-width: 0;
}
.chat-header__name {
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
  /* [ИЗМЕНЕНИЕ] 👇 Обрезаем слишком длинные имена */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chat-header__meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #555;
}

.status-new { color: #3498db; }
.status-read { color: #6f0080; }
.status-in_progress { color: #f39c12; }
.status-closed { color: #95a5a6; }

.chat-header__actions {
  display: flex;
  gap: 0.5rem;
}
.mark-read-btn {
  padding: 0.5rem 1rem;
  font-weight: 500;
  color: #fff;
  background-color: #3498db;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
}
.mark-read-btn:hover { background-color: #2980b9; }
.mark-read-btn:disabled { background-color: #95a5a6; }
.close-lead-btn {
  padding: 0.5rem 1rem;
  font-weight: 500;
  color: #fff;
  background-color: #e74c3c;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
}
.close-lead-btn:hover { background-color: #c0392b; }

.chat-messages {
  flex-grow: 1;
  padding: 1.5rem 1rem;
  overflow-y: auto;
  background-color: #f9f9f9;
}

.loading-state, .error-state, .no-data-state {
  display: flex;
  height: 100%;
  justify-content: center;
  align-items: center;
  font-size: 1.2rem;
  color: #777;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.message-row {
  display: flex;
  margin-bottom: 0.75rem;
}
.message-row.is-manager-row {
  justify-content: flex-end;
}

/* 2. Сам пузырь */
.message-bubble {
  position: relative;
  max-width: 50%;
  padding: 0.6rem 0.9rem;
  padding-bottom: 1.25rem;
  border-radius: 18px;
  background-color: #ffffff;
  color: #333;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  border-bottom-left-radius: 4px;
}

.message-bubble.is-manager-bubble {
  background-color: #1abc9c;
  color: #fff;
  border-bottom-left-radius: 18px;
  border-bottom-right-radius: 4px;
}

.message-bubble__text {
  font-size: 0.95rem;
  white-space: pre-wrap;
}

.message-bubble__meta {
  position: absolute;
  bottom: 4px;
  right: 10px;
  font-size: 0.7rem;
  color: #999;
}
.message-bubble.is-manager-bubble .message-bubble__meta {
  color: #f0f0f0;
  opacity: 0.8;
}

.chat-input-form {
  display: flex;
  padding: 1rem;
  height: 50px;
  border-top: 1px solid #e4e7eb;
  background-color: #fdfdfd;
}
.chat-input {
  flex-grow: 1;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  resize: none;
}
.chat-input:focus {
  outline: none;
  border-color: #1abc9c;
}
.send-button {
  padding: 0 1.5rem;
  margin-left: 1rem;
  font-weight: 600;
  color: #fff;
  background-color: #1abc9c;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.send-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.chat-closed-notice {
  padding: 1rem;
  text-align: center;
  background-color: #f8f9fa;
  color: #777;
  font-weight: 500;
  border-top: 1px solid #e4e7eb;
}
</style>