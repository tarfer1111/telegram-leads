<script lang="ts" setup>
import { RouterView } from 'vue-router';
import Sidebar from '@/components/layout/Sidebar.vue';
import Navbar from '@/components/layout/Navbar.vue';
</script>

<template>
  <div class="default-layout">
    <Sidebar />

    <div class="default-layout__content-wrapper">
      <Navbar />

      <main class="default-layout__main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.default-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: #f0f2f5;
}

.default-layout__content-wrapper {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  height: 100vh;
}

.default-layout__main {
  flex-grow: 1;
  padding: 2rem;
  overflow-y: auto;
}
</style>