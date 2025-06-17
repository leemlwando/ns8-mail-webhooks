<!--
  Webhooks View Component for NS8 Mail Webhooks
  
  Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
  Licensed under GPL-3.0
-->

<template>
  <div>
    <NsPageHeader :title="$t('webhooks.title')">
      <template #actions>
        <NsButton 
          kind="primary" 
          @click="showCreateModal = true"
        >
          <template #icon>
            <NsIcon name="plus" />
          </template>
          {{ $t('webhooks.create_webhook') }}
        </NsButton>
      </template>
    </NsPageHeader>

    <NsCard>
      <template #title>
        {{ $t('webhooks.real_time_webhooks') }}
      </template>
      <template #content>
        <div class="text-center py-8 text-gray-500">
          <NsIcon name="webhook" class="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h3 class="text-lg font-medium mb-2">{{ $t('webhooks.no_webhooks') }}</h3>
          <p class="mb-4">{{ $t('webhooks.no_webhooks_description') }}</p>
          <NsButton @click="showCreateModal = true">
            {{ $t('webhooks.create_first_webhook') }}
          </NsButton>
        </div>
      </template>
    </NsCard>

    <!-- Create Webhook Modal (placeholder) -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-medium mb-4">{{ $t('webhooks.create_webhook') }}</h3>
        <p class="text-gray-600 mb-4">Webhook creation functionality will be implemented here.</p>
        <div class="flex justify-end space-x-3">
          <NsButton kind="secondary" @click="showCreateModal = false">
            {{ $t('common.cancel') }}
          </NsButton>
          <NsButton @click="showCreateModal = false">
            {{ $t('common.create') }}
          </NsButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NsPageHeader, NsCard, NsButton, NsIcon } from '@nethserver/ns8-ui-lib'

export default {
  name: 'Webhooks',
  components: {
    NsPageHeader,
    NsCard,
    NsButton,
    NsIcon
  },
  setup() {
    const { t } = useI18n()
    const showCreateModal = ref(false)

    return {
      showCreateModal
    }
  }
}
</script>
