<!--
  Logs View Component for NS8 Mail Webhooks
  
  Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
  Licensed under GPL-3.0
-->

<template>
  <div>
    <NsPageHeader :title="$t('logs.title')">
      <template #actions>
        <NsButton 
          kind="secondary" 
          @click="refreshLogs"
          :disabled="loading"
        >
          <template #icon>
            <NsIcon :name="loading ? 'spinner' : 'refresh'" />
          </template>
          {{ $t('common.refresh') }}
        </NsButton>
      </template>
    </NsPageHeader>

    <NsCard>
      <template #title>
        {{ $t('logs.webhook_delivery_logs') }}
      </template>
      <template #content>
        <div class="text-center py-8 text-gray-500">
          <NsIcon name="document-text" class="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h3 class="text-lg font-medium mb-2">{{ $t('logs.no_logs') }}</h3>
          <p class="mb-4">{{ $t('logs.no_logs_description') }}</p>
        </div>
      </template>
    </NsCard>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NsPageHeader, NsCard, NsButton, NsIcon } from '@nethserver/ns8-ui-lib'

export default {
  name: 'Logs',
  components: {
    NsPageHeader,
    NsCard,
    NsButton,
    NsIcon
  },
  setup() {
    const { t } = useI18n()
    const loading = ref(false)

    const refreshLogs = () => {
      loading.value = true
      // Simulate API call
      setTimeout(() => {
        loading.value = false
      }, 1000)
    }

    return {
      loading,
      refreshLogs
    }
  }
}
</script>
