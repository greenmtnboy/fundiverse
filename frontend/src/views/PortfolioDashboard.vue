<template>
  <div class="dashboard-container">
    <div v-if="!dashboardReady" class="initializing-state">
      Setting up dashboard...
    </div>

    <Dashboard
      v-else
      class="portfolio-dashboard"
      :name="dashboardId"
      :connection-id="connectionId"
      :view-mode="true"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Dashboard } from '@trilogy-data/trilogy-studio-components/dashboard'
import { useDashboardStore } from '@trilogy-data/trilogy-studio-components/stores'

const props = defineProps<{
  dashboardId: string
  connectionId: string
}>()

const dashboardStore = useDashboardStore()
const dashboardReady = computed(() => Boolean(dashboardStore.dashboards[props.dashboardId]))
</script>

<style scoped>
.dashboard-container {
  width: 100%;
  height: 100%;
  min-height: 0;
}

.initializing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  min-height: 200px;
  justify-content: center;
  font-size: 16px;
  color: #999;
}

.portfolio-dashboard {
  width: 100%;
  height: 100%;
}

.portfolio-dashboard :deep(.dashboard-controls) {
  display: none;
}

.portfolio-dashboard :deep(.grid-container) {
  padding: 0;
  background: transparent;
}

.portfolio-dashboard :deep(.grid-content) {
  max-width: none !important;
}
</style>
