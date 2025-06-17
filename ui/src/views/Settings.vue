<!--
  Settings View Component for NS8 Mail Webhooks
  
  Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
  Licensed under GPL-3.0
-->

<template>
  <div>
    <NsPageHeader :title="$t('settings.title')">
      <template #actions>
        <NsButton 
          kind="primary" 
          @click="saveSettings"
          :disabled="loading"
        >
          <template #icon>
            <NsIcon :name="loading ? 'spinner' : 'save'" />
          </template>
          {{ $t('common.save') }}
        </NsButton>
      </template>
    </NsPageHeader>

    <div class="space-y-6">
      <!-- General Configuration -->
      <NsCard>
        <template #title>
          {{ $t('settings.general') }}
        </template>
        <template #content>
          <div class="space-y-4">
            <NsFormGroup>
              <template #label>
                {{ $t('settings.module_name') }}
              </template>
              <NsTextInput 
                v-model="settings.module_name"
                :placeholder="$t('settings.module_name_placeholder')"
              />
            </NsFormGroup>

            <NsFormGroup>
              <template #label>
                {{ $t('settings.log_level') }}
              </template>
              <NsComboBox
                v-model="settings.log_level"
                :options="logLevelOptions"
                :placeholder="$t('settings.select_log_level')"
              />
            </NsFormGroup>

            <NsFormGroup>
              <template #label>
                {{ $t('settings.max_concurrent_deliveries') }}
              </template>
              <NsNumberInput 
                v-model="settings.max_concurrent_deliveries"
                :min="1"
                :max="50"
              />
              <template #helper>
                {{ $t('settings.max_concurrent_deliveries_help') }}
              </template>
            </NsFormGroup>
          </div>
        </template>
      </NsCard>

      <!-- Webhook Defaults -->
      <NsCard>
        <template #title>
          {{ $t('settings.webhook_defaults') }}
        </template>
        <template #content>
          <div class="space-y-4">
            <NsFormGroup>
              <template #label>
                {{ $t('settings.default_timeout') }}
              </template>
              <NsNumberInput 
                v-model="settings.default_timeout"
                :min="5"
                :max="300"
              />
              <template #helper>
                {{ $t('settings.default_timeout_help') }}
              </template>
            </NsFormGroup>

            <NsFormGroup>
              <template #label>
                {{ $t('settings.default_retry_attempts') }}
              </template>
              <NsNumberInput 
                v-model="settings.default_retry_attempts"
                :min="0"
                :max="10"
              />
            </NsFormGroup>

            <NsFormGroup>
              <template #label>
                {{ $t('settings.retry_delay') }}
              </template>
              <NsNumberInput 
                v-model="settings.retry_delay"
                :min="1"
                :max="3600"
              />
              <template #helper>
                {{ $t('settings.retry_delay_help') }}
              </template>
            </NsFormGroup>
          </div>
        </template>
      </NsCard>

      <!-- Security Settings -->
      <NsCard>
        <template #title>
          {{ $t('settings.security') }}
        </template>
        <template #content>
          <div class="space-y-4">
            <NsFormGroup>
              <NsToggle 
                v-model="settings.require_tls"
                :label="$t('settings.require_tls')"
              />
              <template #helper>
                {{ $t('settings.require_tls_help') }}
              </template>
            </NsFormGroup>

            <NsFormGroup>
              <NsToggle 
                v-model="settings.verify_ssl_certificates"
                :label="$t('settings.verify_ssl_certificates')"
              />
              <template #helper>
                {{ $t('settings.verify_ssl_certificates_help') }}
              </template>
            </NsFormGroup>

            <NsFormGroup>
              <template #label>
                {{ $t('settings.allowed_hosts') }}
              </template>
              <NsTextArea 
                v-model="settings.allowed_hosts"
                :placeholder="$t('settings.allowed_hosts_placeholder')"
                rows="3"
              />
              <template #helper>
                {{ $t('settings.allowed_hosts_help') }}
              </template>
            </NsFormGroup>
          </div>
        </template>
      </NsCard>

      <!-- Performance Tuning -->
      <NsCard>
        <template #title>
          {{ $t('settings.performance') }}
        </template>
        <template #content>
          <div class="space-y-4">
            <NsFormGroup>
              <template #label>
                {{ $t('settings.batch_size') }}
              </template>
              <NsNumberInput 
                v-model="settings.batch_size"
                :min="1"
                :max="100"
              />
              <template #helper>
                {{ $t('settings.batch_size_help') }}
              </template>
            </NsFormGroup>

            <NsFormGroup>
              <template #label>
                {{ $t('settings.log_retention_days') }}
              </template>
              <NsNumberInput 
                v-model="settings.log_retention_days"
                :min="1"
                :max="365"
              />
            </NsFormGroup>

            <NsFormGroup>
              <template #label>
                {{ $t('settings.api_memory_limit') }}
              </template>
              <NsComboBox
                v-model="settings.api_memory_limit"
                :options="memoryLimitOptions"
              />
            </NsFormGroup>
          </div>
        </template>
      </NsCard>
    </div>
  </div>
</template>

<script>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  NsPageHeader, 
  NsCard, 
  NsButton, 
  NsIcon,
  NsFormGroup,
  NsTextInput,
  NsNumberInput,
  NsTextArea,
  NsComboBox,
  NsToggle
} from '@nethserver/ns8-ui-lib'

export default {
  name: 'Settings',
  components: {
    NsPageHeader,
    NsCard,
    NsButton,
    NsIcon,
    NsFormGroup,
    NsTextInput,
    NsNumberInput,
    NsTextArea,
    NsComboBox,
    NsToggle
  },
  setup() {
    const { t } = useI18n()
    const loading = ref(false)
    
    const settings = ref({
      module_name: '',
      log_level: 'info',
      max_concurrent_deliveries: 10,
      default_timeout: 30,
      default_retry_attempts: 3,
      retry_delay: 60,
      require_tls: true,
      verify_ssl_certificates: true,
      allowed_hosts: '',
      batch_size: 10,
      log_retention_days: 30,
      api_memory_limit: '256M'
    })

    const logLevelOptions = [
      { id: 'debug', label: t('settings.log_level_debug') },
      { id: 'info', label: t('settings.log_level_info') },
      { id: 'warn', label: t('settings.log_level_warn') },
      { id: 'error', label: t('settings.log_level_error') }
    ]

    const memoryLimitOptions = [
      { id: '128M', label: '128 MB' },
      { id: '256M', label: '256 MB' },
      { id: '512M', label: '512 MB' },
      { id: '1G', label: '1 GB' }
    ]

    const fetchSettings = async () => {
      try {
        const response = await window.nethserver.exec(['get-configuration'], {})
        if (response.status === 'success') {
          Object.assign(settings.value, response.configuration)
        }
      } catch (error) {
        console.error('Failed to fetch settings:', error)
      }
    }

    const saveSettings = async () => {
      loading.value = true
      try {
        const response = await window.nethserver.exec(['configure-module'], settings.value)
        if (response.status === 'success') {
          window.nethserver?.notification?.success({
            title: t('settings.save_success'),
            message: t('settings.save_success_message')
          })
        } else {
          throw new Error(response.error || 'Configuration failed')
        }
      } catch (error) {
        console.error('Failed to save settings:', error)
        window.nethserver?.notification?.error({
          title: t('settings.save_error'),
          message: error.message
        })
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      fetchSettings()
    })

    return {
      loading,
      settings,
      logLevelOptions,
      memoryLimitOptions,
      saveSettings
    }
  }
}
</script>
