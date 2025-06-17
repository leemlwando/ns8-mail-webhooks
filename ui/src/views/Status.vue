<!--
  Status View Component for NS8 Mail Webhooks
  
  Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
  Licensed under GPL-3.0
-->

<template>
  <div>
    <NsPageHeader :title="$t('status.title')">
      <template #actions>
        <NsButton 
          kind="secondary" 
          @click="refresh"
          :disabled="loading"
        >
          <template #icon>
            <NsIcon :name="loading ? 'spinner' : 'refresh'" />
          </template>
          {{ $t('common.refresh') }}
        </NsButton>
      </template>
    </NsPageHeader>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Module Status Card -->
      <NsCard>
        <template #title>
          {{ $t('status.module_status') }}
        </template>
        <template #content>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span>{{ $t('status.webhook_service') }}</span>
              <NsBadge 
                :kind="getServiceStatusKind(moduleStatus.webhook_service)"
                :text="getServiceStatusText(moduleStatus.webhook_service)"
              />
            </div>
            
            <div class="flex items-center justify-between">
              <span>{{ $t('status.deno_api') }}</span>
              <NsBadge 
                :kind="getServiceStatusKind(moduleStatus.deno_api)"
                :text="getServiceStatusText(moduleStatus.deno_api)"
              />
            </div>
            
            <div class="flex items-center justify-between">
              <span>{{ $t('status.event_bridge') }}</span>
              <NsBadge 
                :kind="getServiceStatusKind(moduleStatus.event_bridge)"
                :text="getServiceStatusText(moduleStatus.event_bridge)"
              />
            </div>

            <div class="flex items-center justify-between">
              <span>{{ $t('status.scheduler') }}</span>
              <NsBadge 
                :kind="getServiceStatusKind(moduleStatus.scheduler)"
                :text="getServiceStatusText(moduleStatus.scheduler)"
              />
            </div>
          </div>
        </template>
      </NsCard>

      <!-- Statistics Card -->
      <NsCard>
        <template #title>
          {{ $t('status.statistics') }}
        </template>
        <template #content>
          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">
                  {{ statistics.total_webhooks }}
                </div>
                <div class="text-sm text-gray-600">
                  {{ $t('status.total_webhooks') }}
                </div>
              </div>
              
              <div class="text-center">
                <div class="text-2xl font-bold text-green-600">
                  {{ statistics.active_webhooks }}
                </div>
                <div class="text-sm text-gray-600">
                  {{ $t('status.active_webhooks') }}
                </div>
              </div>
              
              <div class="text-center">
                <div class="text-2xl font-bold text-yellow-600">
                  {{ statistics.deliveries_24h }}
                </div>
                <div class="text-sm text-gray-600">
                  {{ $t('status.deliveries_24h') }}
                </div>
              </div>
              
              <div class="text-center">
                <div class="text-2xl font-bold" :class="getSuccessRateClass(statistics.success_rate)">
                  {{ statistics.success_rate }}%
                </div>
                <div class="text-sm text-gray-600">
                  {{ $t('status.success_rate') }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </NsCard>

      <!-- Health Check Details -->
      <NsCard v-if="healthDetails.length > 0" class="lg:col-span-2">
        <template #title>
          {{ $t('status.health_details') }}
        </template>
        <template #content>
          <div class="space-y-3">
            <div 
              v-for="check in healthDetails" 
              :key="check.component"
              class="flex items-center justify-between p-3 border rounded"
            >
              <div class="flex items-center space-x-3">
                <NsIcon 
                  :name="getHealthIcon(check.status)" 
                  :class="getHealthIconClass(check.status)"
                />
                <div>
                  <div class="font-medium">{{ check.component }}</div>
                  <div class="text-sm text-gray-600">{{ check.message }}</div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-sm text-gray-500">
                  {{ $t('status.last_check') }}: {{ formatDate(check.timestamp) }}
                </div>
                <div v-if="check.response_time" class="text-xs text-gray-400">
                  {{ check.response_time }}ms
                </div>
              </div>
            </div>
          </div>
        </template>
      </NsCard>
    </div>

    <!-- Recent Activity -->
    <NsCard class="mt-6">
      <template #title>
        {{ $t('status.recent_activity') }}
      </template>
      <template #content>
        <div v-if="recentActivity.length === 0" class="text-center py-8 text-gray-500">
          {{ $t('status.no_recent_activity') }}
        </div>
        <div v-else class="space-y-3">
          <div 
            v-for="activity in recentActivity" 
            :key="activity.id"
            class="flex items-center justify-between p-3 border-l-4"
            :class="getActivityBorderClass(activity.type)"
          >
            <div class="flex items-center space-x-3">
              <NsIcon 
                :name="getActivityIcon(activity.type)" 
                :class="getActivityIconClass(activity.type)"
              />
              <div>
                <div class="font-medium">{{ activity.message }}</div>
                <div class="text-sm text-gray-600">{{ activity.details }}</div>
              </div>
            </div>
            <div class="text-sm text-gray-500">
              {{ formatDate(activity.timestamp) }}
            </div>
          </div>
        </div>
      </template>
    </NsCard>
  </div>
</template>

<script>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NsPageHeader, NsCard, NsButton, NsIcon, NsBadge } from '@nethserver/ns8-ui-lib'

export default {
  name: 'Status',
  components: {
    NsPageHeader,
    NsCard,
    NsButton,
    NsIcon,
    NsBadge
  },
  setup() {
    const { t } = useI18n()
    const loading = ref(false)
    const moduleStatus = ref({
      webhook_service: 'unknown',
      deno_api: 'unknown',
      event_bridge: 'unknown',
      scheduler: 'unknown'
    })
    const statistics = ref({
      total_webhooks: 0,
      active_webhooks: 0,
      deliveries_24h: 0,
      success_rate: 0
    })
    const healthDetails = ref([])
    const recentActivity = ref([])

    const getServiceStatusKind = (status) => {
      const statusMap = {
        'running': 'success',
        'healthy': 'success',
        'stopped': 'error',
        'error': 'error',
        'starting': 'warning',
        'unknown': 'neutral'
      }
      return statusMap[status] || 'neutral'
    }

    const getServiceStatusText = (status) => {
      return t(`status.service_${status}`)
    }

    const getSuccessRateClass = (rate) => {
      if (rate >= 95) return 'text-green-600'
      if (rate >= 80) return 'text-yellow-600'
      return 'text-red-600'
    }

    const getHealthIcon = (status) => {
      const iconMap = {
        'healthy': 'check-circle',
        'warning': 'exclamation-triangle',
        'error': 'x-circle',
        'unknown': 'question-mark-circle'
      }
      return iconMap[status] || 'question-mark-circle'
    }

    const getHealthIconClass = (status) => {
      const classMap = {
        'healthy': 'text-green-500',
        'warning': 'text-yellow-500',
        'error': 'text-red-500',
        'unknown': 'text-gray-500'
      }
      return classMap[status] || 'text-gray-500'
    }

    const getActivityIcon = (type) => {
      const iconMap = {
        'webhook_created': 'plus-circle',
        'webhook_triggered': 'paper-airplane',
        'webhook_failed': 'x-circle',
        'service_restarted': 'refresh'
      }
      return iconMap[type] || 'information-circle'
    }

    const getActivityIconClass = (type) => {
      const classMap = {
        'webhook_created': 'text-blue-500',
        'webhook_triggered': 'text-green-500',
        'webhook_failed': 'text-red-500',
        'service_restarted': 'text-yellow-500'
      }
      return classMap[type] || 'text-gray-500'
    }

    const getActivityBorderClass = (type) => {
      const classMap = {
        'webhook_created': 'border-blue-500',
        'webhook_triggered': 'border-green-500',
        'webhook_failed': 'border-red-500',
        'service_restarted': 'border-yellow-500'
      }
      return classMap[type] || 'border-gray-500'
    }

    const formatDate = (timestamp) => {
      return new Date(timestamp).toLocaleString()
    }

    const fetchStatus = async () => {
      loading.value = true
      try {
        // Call the status action using NS8 API
        const response = await window.nethserver.exec(['get-status'], {})
        
        if (response.status === 'success') {
          moduleStatus.value = response.module_status
          statistics.value = response.statistics
          healthDetails.value = response.health_details || []
          recentActivity.value = response.recent_activity || []
        }
      } catch (error) {
        console.error('Failed to fetch status:', error)
        // Show error notification
        window.nethserver?.notification?.error({
          title: t('status.fetch_error'),
          message: error.message
        })
      } finally {
        loading.value = false
      }
    }

    const refresh = () => {
      fetchStatus()
    }

    onMounted(() => {
      fetchStatus()
      // Set up auto-refresh every 30 seconds
      setInterval(fetchStatus, 30000)
    })

    return {
      loading,
      moduleStatus,
      statistics,
      healthDetails,
      recentActivity,
      getServiceStatusKind,
      getServiceStatusText,
      getSuccessRateClass,
      getHealthIcon,
      getHealthIconClass,
      getActivityIcon,
      getActivityIconClass,
      getActivityBorderClass,
      formatDate,
      refresh
    }
  }
}
</script>
