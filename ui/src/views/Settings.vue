<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <div class="settings-container">
    <div class="settings-content">
      <div class="page-title">
        <h2>{{ $t("settings.title") }}</h2>
        <p>{{ $t("settings.description") }}</p>
      </div>

      <cv-loading v-if="loading.getConfiguration" />

      <div v-else class="settings-sections">
        <!-- Mail Server Configuration Section -->
        <cv-tile class="settings-section">
          <h3>{{ $t("settings.mail_server_config") }}</h3>
          <p>{{ $t("settings.mail_server_description") }}</p>
          
          <cv-form class="settings-form">
            <div class="form-grid">
              <cv-text-input
                v-model="config.imapHost"
                :label="$t('settings.imap_host')"
                :placeholder="$t('settings.imap_host_placeholder')"
                :disabled="loading.configureModule"
                :invalid="errors.imapHost"
                :invalid-message="errors.imapHost"
              />
              
              <cv-text-input
                v-model="config.imapPort"
                :label="$t('settings.imap_port')"
                :placeholder="993"
                type="number"
                :disabled="loading.configureModule"
                :invalid="errors.imapPort"
                :invalid-message="errors.imapPort"
              />
            </div>

            <cv-checkbox
              v-model="config.imapSsl"
              :label="$t('settings.use_ssl')"
              :disabled="loading.configureModule"
            />

            <cv-text-input
              v-model="config.defaultUsername"
              :label="$t('settings.default_username')"
              :placeholder="$t('settings.default_username_placeholder')"
              :helper-text="$t('settings.default_username_help')"
              :disabled="loading.configureModule"
            />
          </cv-form>
        </cv-tile>

        <!-- Security Settings Section -->
        <cv-tile class="settings-section">
          <h3>{{ $t("settings.security_settings") }}</h3>
          <p>{{ $t("settings.security_description") }}</p>
          
          <cv-form class="settings-form">
            <cv-text-input
              v-model="config.defaultApiKey"
              :label="$t('settings.default_api_key')"
              :placeholder="$t('settings.default_api_key_placeholder')"
              :helper-text="$t('settings.default_api_key_help')"
              type="password"
              :disabled="loading.configureModule"
            />

            <div class="form-grid">
              <cv-number-input
                v-model="config.webhookTimeout"
                :label="$t('settings.webhook_timeout')"
                :helper-text="$t('settings.webhook_timeout_help')"
                :min="5"
                :max="300"
                :disabled="loading.configureModule"
              />

              <cv-number-input
                v-model="config.maxRetries"
                :label="$t('settings.max_retries')"
                :helper-text="$t('settings.max_retries_help')"
                :min="0"
                :max="10"
                :disabled="loading.configureModule"
              />
            </div>

            <cv-checkbox
              v-model="config.validateSslCertificates"
              :label="$t('settings.validate_ssl_certificates')"
              :disabled="loading.configureModule"
            />
          </cv-form>
        </cv-tile>

        <!-- Performance Settings Section -->
        <cv-tile class="settings-section">
          <h3>{{ $t("settings.performance_settings") }}</h3>
          <p>{{ $t("settings.performance_description") }}</p>
          
          <cv-form class="settings-form">
            <div class="form-grid">
              <cv-number-input
                v-model="config.maxEmailsPerBatch"
                :label="$t('settings.max_emails_per_batch')"
                :helper-text="$t('settings.max_emails_per_batch_help')"
                :min="1"
                :max="1000"
                :disabled="loading.configureModule"
              />

              <cv-number-input
                v-model="config.batchProcessingDelay"
                :label="$t('settings.batch_processing_delay')"
                :helper-text="$t('settings.batch_processing_delay_help')"
                :min="100"
                :max="10000"
                :disabled="loading.configureModule"
              />
            </div>

            <cv-number-input
              v-model="config.connectionPoolSize"
              :label="$t('settings.connection_pool_size')"
              :helper-text="$t('settings.connection_pool_size_help')"
              :min="1"
              :max="20"
              :disabled="loading.configureModule"
            />
          </cv-form>
        </cv-tile>

        <!-- Logging Configuration Section -->
        <cv-tile class="settings-section">
          <h3>{{ $t("settings.logging_config") }}</h3>
          <p>{{ $t("settings.logging_description") }}</p>
          
          <cv-form class="settings-form">
            <cv-dropdown
              v-model="config.logLevel"
              :label="$t('settings.log_level')"
              :disabled="loading.configureModule"
            >
              <cv-dropdown-item value="ERROR">ERROR</cv-dropdown-item>
              <cv-dropdown-item value="WARN">WARN</cv-dropdown-item>
              <cv-dropdown-item value="INFO">INFO</cv-dropdown-item>
              <cv-dropdown-item value="DEBUG">DEBUG</cv-dropdown-item>
            </cv-dropdown>

            <div class="form-grid">
              <cv-number-input
                v-model="config.logRetentionDays"
                :label="$t('settings.log_retention_days')"
                :helper-text="$t('settings.log_retention_help')"
                :min="1"
                :max="365"
                :disabled="loading.configureModule"
              />

              <cv-number-input
                v-model="config.maxLogFileSize"
                :label="$t('settings.max_log_file_size')"
                :helper-text="$t('settings.max_log_file_size_help')"
                :min="1"
                :max="100"
                :disabled="loading.configureModule"
              />
            </div>

            <cv-checkbox
              v-model="config.enableVerboseLogging"
              :label="$t('settings.enable_verbose_logging')"
              :disabled="loading.configureModule"
            />
          </cv-form>
        </cv-tile>

        <!-- Module Information Section -->
        <cv-tile class="settings-section">
          <h3>{{ $t("settings.module_info") }}</h3>
          <p>{{ $t("settings.module_info_description") }}</p>
          
          <div class="info-grid">
            <div class="info-item">
              <strong>{{ $t("settings.module_version") }}:</strong>
              <span>{{ moduleInfo.version || "N/A" }}</span>
            </div>
            <div class="info-item">
              <strong>{{ $t("settings.module_status") }}:</strong>
              <cv-tag
                :kind="moduleInfo.status === 'running' ? 'green' : 'red'"
                :label="moduleInfo.status || 'unknown'"
              />
            </div>
            <div class="info-item">
              <strong>{{ $t("settings.last_updated") }}:</strong>
              <span>{{ formatDateTime(moduleInfo.lastUpdated) }}</span>
            </div>
            <div class="info-item">
              <strong>{{ $t("settings.active_triggers") }}:</strong>
              <span>{{ moduleInfo.activeTriggers || 0 }}</span>
            </div>
          </div>

          <div class="diagnostics-section">
            <cv-button
              kind="secondary"
              @click="runDiagnostics"
              :loading="loading.diagnostics"
              :disabled="loading.configureModule"
            >
              {{ $t("settings.run_diagnostics") }}
            </cv-button>
            
            <cv-button
              kind="tertiary"
              @click="exportLogs"
              :loading="loading.exportLogs"
              :disabled="loading.configureModule"
            >
              {{ $t("settings.export_logs") }}
            </cv-button>
          </div>
        </cv-tile>

        <!-- Error Display -->
        <cv-inline-notification
          v-if="error.configureModule"
          kind="error"
          :title="$t('settings.configuration_error')"
          :subtitle="error.configureModule"
          @close="error.configureModule = ''"
        />

        <!-- Save Button -->
        <div class="settings-actions">
          <cv-button
            kind="primary"
            @click="saveConfiguration"
            :loading="loading.configureModule"
            :disabled="!isFormValid || loading.configureModule"
          >
            {{ $t("settings.save_configuration") }}
          </cv-button>
          
          <cv-button
            kind="secondary"
            @click="resetToDefaults"
            :disabled="loading.configureModule"
          >
            {{ $t("settings.reset_to_defaults") }}
          </cv-button>        </div>
      </div>
    </div>
  </div>
</template>

<script>
import to from "await-to-js";
import { mapState } from "vuex";
import axios from "axios";
import {
  UtilService,
  TaskService,
  IconService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";

export default {
  name: "Settings",
  mixins: [TaskService, IconService, UtilService, PageTitleService],
  pageTitle() {
    return this.$t("settings.title") + " - " + this.appName;
  },
  data() {
    return {
      config: {
        // Mail Server Configuration
        imapHost: "localhost",
        imapPort: 993,
        imapSsl: true,
        defaultUsername: "",
        
        // Security Settings
        defaultApiKey: "",
        webhookTimeout: 30,
        maxRetries: 3,
        validateSslCertificates: true,
        
        // Performance Settings
        maxEmailsPerBatch: 50,
        batchProcessingDelay: 1000,
        connectionPoolSize: 5,
        
        // Logging Configuration
        logLevel: "INFO",
        logRetentionDays: 30,
        maxLogFileSize: 10,
        enableVerboseLogging: false,
      },
      moduleInfo: {
        version: "",
        status: "",
        lastUpdated: "",
        activeTriggers: 0,
      },
      loading: {
        getConfiguration: false,
        configureModule: false,
        diagnostics: false,
        exportLogs: false,
      },
      errors: {
        imapHost: "",
        imapPort: "",
      },
      error: {
        configureModule: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
    isFormValid() {
      return (
        this.config.imapHost &&
        this.config.imapPort &&
        this.config.imapPort > 0 &&
        this.config.imapPort <= 65535 &&
        this.validateForm()
      );
    },
  },
  created() {
    this.getConfiguration();
    this.getModuleInfo();
  },
  methods: {
    validateForm() {
      this.errors = {};
      let isValid = true;

      if (!this.config.imapHost) {
        this.errors.imapHost = this.$t("common.required");
        isValid = false;
      }

      if (!this.config.imapPort || this.config.imapPort < 1 || this.config.imapPort > 65535) {
        this.errors.imapPort = this.$t("settings.invalid_port");
        isValid = false;
      }

      return isValid;
    },    async getConfiguration() {
      this.loading.getConfiguration = true;
      this.error.getConfiguration = "";
      
      try {
        const res = await axios.get('/api/config');
        if (res.data) {
          this.config = { ...this.config, ...res.data };
        }
      } catch (error) {
        console.error('Error loading configuration:', error);
        // Fall back to defaults
      }
      
      this.loading.getConfiguration = false;
    },    async getModuleInfo() {
      try {
        const healthRes = await axios.get('/api/health');
        const statsRes = await axios.get('/api/stats');
        
        this.moduleInfo = {
          version: "1.0.0", // Could be retrieved from backend
          status: healthRes.data.status === 'ok' ? 'running' : 'stopped',
          lastUpdated: new Date().toISOString(),
          activeTriggers: statsRes.data.total_triggers || 0,
        };
      } catch (error) {
        console.error('Error loading module info:', error);
        this.moduleInfo = {
          version: "N/A",
          status: "unknown",
          lastUpdated: "",
          activeTriggers: 0,
        };
      }
    },async saveConfiguration() {
      if (!this.validateForm()) return;

      this.loading.configureModule = true;
      this.error.configureModule = "";
      
      try {
        await axios.put('/api/config', this.config);
        this.createSuccessNotificationForApp(this.$t("settings.configuration_saved"));
      } catch (error) {
        this.error.configureModule = error.response?.data?.detail || error.message || this.$t("settings.save_error");
      }
      
      this.loading.configureModule = false;
    },
    resetToDefaults() {
      this.config = {
        imapHost: "localhost",
        imapPort: 993,
        imapSsl: true,
        defaultUsername: "",
        defaultApiKey: "",
        webhookTimeout: 30,
        maxRetries: 3,
        validateSslCertificates: true,
        maxEmailsPerBatch: 50,
        batchProcessingDelay: 1000,
        connectionPoolSize: 5,
        logLevel: "INFO",
        logRetentionDays: 30,
        maxLogFileSize: 10,
        enableVerboseLogging: false,
      };
    },
    async runDiagnostics() {
      this.loading.diagnostics = true;
      
      const taskAction = "run-diagnostics";
      const eventId = this.getUuid();

      this.$root.$once(`${taskAction}-completed-${eventId}`, this.runDiagnosticsCompleted);

      await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          extra: {
            title: this.$t("action." + taskAction),
            eventId,
          },
        })
      );
    },
    runDiagnosticsCompleted(taskContext, taskResult) {
      this.loading.diagnostics = false;
      if (taskResult.output && taskResult.output.success) {
        this.createSuccessNotificationForApp(this.$t("settings.diagnostics_success"));
      } else {
        this.createErrorNotificationForApp(
          { message: taskResult.output?.error || "Diagnostics failed" },
          this.$t("settings.diagnostics_error")
        );
      }
    },
    async exportLogs() {
      this.loading.exportLogs = true;
      
      const taskAction = "export-logs";
      const eventId = this.getUuid();

      this.$root.$once(`${taskAction}-completed-${eventId}`, this.exportLogsCompleted);

      await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          extra: {
            title: this.$t("action." + taskAction),
            eventId,
          },
        })
      );
    },
    exportLogsCompleted(taskContext, taskResult) {
      this.loading.exportLogs = false;
      if (taskResult.output && taskResult.output.downloadUrl) {
        // Trigger download
        const link = document.createElement("a");
        link.href = taskResult.output.downloadUrl;
        link.download = `ns8-mail-webhook-logs-${new Date().toISOString().split('T')[0]}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.createSuccessNotificationForApp(this.$t("settings.logs_exported"));
      } else {
        this.createErrorNotificationForApp(
          { message: "Export failed" },
          this.$t("settings.export_error")
        );
      }    },
    formatDateTime(timestamp) {
      if (!timestamp) return this.$t("common.never");
      return new Date(timestamp).toLocaleString();
    },
  },
};
</script>

<style scoped lang="scss">
@import "@/styles/carbon-utils";

.settings-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.settings-content {
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
}

.page-title {
  margin-bottom: 2rem;
}

.page-title h2 {
  margin: 0 0 0.5rem 0;
  font-weight: 400;
}

.page-title p {
  margin: 0;
  color: #525252;
}

.settings-sections {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-section {
  margin-bottom: 0;
}

.settings-section h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.settings-section p {
  margin: 0 0 1rem 0;
  color: #525252;
  font-size: 0.875rem;
}

.settings-form {
  margin-top: 1rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e0e0e0;
}

.info-item strong {
  font-weight: 600;
}

.diagnostics-section {
  display: flex;
  gap: 1rem;
}

.settings-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

@media (max-width: 768px) {
  .form-grid,
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .diagnostics-section,
  .settings-actions {
    flex-direction: column;
  }
}
</style>
