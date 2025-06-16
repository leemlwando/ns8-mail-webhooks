<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <div class="one-time-job">
    <div class="description-section">
      <p>{{ $t("mail_webhooks.one_time_job_description") }}</p>
    </div>

    <cv-form @submit.prevent="runJob" class="job-form">
      <div class="form-grid">
        <div class="form-column">
          <cv-dropdown
            v-model="jobForm.mailbox"
            :label="$t('mail_webhooks.mailbox')"
            :placeholder="$t('mail_webhooks.select_mailbox')"
            :disabled="loading.mailboxes || jobRunning"
            :invalid="jobFormErrors.mailbox"
            :invalid-message="jobFormErrors.mailbox"
          >
            <cv-dropdown-item
              v-for="mailbox in mailboxes"
              :key="mailbox.id"
              :value="mailbox.id"
            >
              {{ mailbox.name }}
            </cv-dropdown-item>
          </cv-dropdown>

          <cv-text-input
            v-model="jobForm.webhookUrl"
            :label="$t('mail_webhooks.webhook_url')"
            :placeholder="$t('mail_webhooks.webhook_url_placeholder')"
            :disabled="jobRunning"
            :invalid="jobFormErrors.webhookUrl"
            :invalid-message="jobFormErrors.webhookUrl"
          />

          <cv-text-input
            v-model="jobForm.apiKey"
            :label="$t('mail_webhooks.api_key_optional')"
            :placeholder="$t('mail_webhooks.api_key_placeholder')"
            type="password"
            :disabled="jobRunning"
          />
        </div>

        <div class="form-column">
          <cv-dropdown
            v-model="jobForm.payloadFormat"
            :label="$t('mail_webhooks.payload_format')"
            :disabled="jobRunning"
          >
            <cv-dropdown-item value="raw">
              {{ $t("mail_webhooks.payload_format_raw") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="json">
              {{ $t("mail_webhooks.payload_format_json") }}
            </cv-dropdown-item>
          </cv-dropdown>

          <cv-dropdown
            v-model="jobForm.postProcessing"
            :label="$t('mail_webhooks.post_processing')"
            :disabled="jobRunning"
          >
            <cv-dropdown-item value="mark_read">
              {{ $t("mail_webhooks.post_processing_mark_read") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="delete">
              {{ $t("mail_webhooks.post_processing_delete") }}
            </cv-dropdown-item>
          </cv-dropdown>
        </div>
      </div>

      <div class="form-actions">
        <cv-button
          kind="primary"
          type="submit"
          :disabled="!isFormValid || jobRunning"
          :loading="jobRunning"
        >
          {{ jobRunning ? $t("mail_webhooks.job_running") : $t("mail_webhooks.run_now") }}
        </cv-button>
      </div>
    </cv-form>

    <!-- Job Status Section -->
    <div v-if="jobStatus" class="job-status-section">
      <cv-tile :class="jobStatusClass">
        <div class="job-status-content">
          <div class="job-status-header">
            <h4>{{ jobStatusTitle }}</h4>
            <div v-if="jobRunning" class="job-progress">
              <cv-progress-bar 
                :value="jobProgress" 
                :max="100"
                :label="jobProgressLabel"
              />
            </div>
          </div>
          
          <div v-if="jobStatus.details" class="job-details">
            <p><strong>{{ $t("mail_webhooks.mailbox") }}:</strong> {{ jobStatus.mailbox }}</p>
            <p><strong>{{ $t("mail_webhooks.webhook_url") }}:</strong> {{ jobStatus.webhookUrl }}</p>
            <p v-if="jobStatus.emailsProcessed !== undefined">
              <strong>Emails processed:</strong> {{ jobStatus.emailsProcessed }}
            </p>
            <p v-if="jobStatus.startTime">
              <strong>Started:</strong> {{ formatDateTime(jobStatus.startTime) }}
            </p>
            <p v-if="jobStatus.endTime">
              <strong>Completed:</strong> {{ formatDateTime(jobStatus.endTime) }}
            </p>
          </div>

          <div v-if="jobStatus.error" class="job-error">
            <p><strong>Error:</strong> {{ jobStatus.error }}</p>
          </div>

          <div v-if="jobStatus.logs && jobStatus.logs.length > 0" class="job-logs">
            <h5>Job Logs:</h5>
            <div class="logs-container">
              <div 
                v-for="(log, index) in jobStatus.logs" 
                :key="index" 
                :class="['log-entry', log.level]"
              >
                <span class="log-timestamp">{{ formatTime(log.timestamp) }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </cv-tile>
    </div>

    <!-- Destructive Action Confirmation Modal -->
    <cv-modal
      :visible="showDestructiveWarning"
      @modal-hide-request="showDestructiveWarning = false"
      kind="danger"
      size="small"
    >
      <template v-slot:title>{{ $t("mail_webhooks.post_processing") }}</template>
      <template v-slot:content>
        <p>{{ $t("mail_webhooks.confirm_delete_destructive") }}</p>
      </template>
      <template v-slot:secondary-button>{{ $t("common.cancel") }}</template>
      <template v-slot:primary-button>{{ $t("common.yes") }}</template>
      <template v-slot:primary-button-action>
        <cv-button
          kind="danger"
          @click="confirmRunJob"
        >
          {{ $t("common.yes") }}
        </cv-button>
      </template>
    </cv-modal>
  </div>
</template>

<script>
import { UtilService, TaskService } from "@nethserver/ns8-ui-lib";
import to from "await-to-js";

export default {
  name: "OneTimeJob",
  props: {
    mailboxes: {
      type: Array,
      default: () => [],
    },
    loading: {
      type: Object,
      default: () => ({}),
    },
  },
  mixins: [UtilService, TaskService],
  data() {
    return {
      jobForm: this.getEmptyJobForm(),
      jobFormErrors: {},
      jobRunning: false,
      jobStatus: null,
      jobProgress: 0,
      jobProgressLabel: "",
      showDestructiveWarning: false,
      jobStatusPollingInterval: null,
    };
  },
  computed: {
    isFormValid() {
      return (
        this.jobForm.mailbox &&
        this.jobForm.webhookUrl &&
        this.jobForm.payloadFormat &&
        this.jobForm.postProcessing &&
        this.validateForm()
      );
    },
    jobStatusClass() {
      if (!this.jobStatus) return "";
      
      switch (this.jobStatus.status) {
        case "running":
          return "job-status-running";
        case "completed":
          return "job-status-success";
        case "failed":
          return "job-status-error";
        default:
          return "";
      }
    },
    jobStatusTitle() {
      if (!this.jobStatus) return "";
      
      switch (this.jobStatus.status) {
        case "running":
          return this.$t("mail_webhooks.job_running");
        case "completed":
          return this.$t("mail_webhooks.job_completed");
        case "failed":
          return this.$t("mail_webhooks.job_failed");
        default:
          return "";
      }
    },
  },
  beforeDestroy() {
    if (this.jobStatusPollingInterval) {
      clearInterval(this.jobStatusPollingInterval);
    }
  },
  methods: {
    getEmptyJobForm() {
      return {
        mailbox: "",
        webhookUrl: "",
        apiKey: "",
        payloadFormat: "json",
        postProcessing: "mark_read",
      };
    },
    validateForm() {
      this.jobFormErrors = {};
      let isValid = true;

      if (!this.jobForm.mailbox) {
        this.jobFormErrors.mailbox = this.$t("common.required");
        isValid = false;
      }

      if (!this.jobForm.webhookUrl) {
        this.jobFormErrors.webhookUrl = this.$t("common.required");
        isValid = false;
      } else {
        try {
          new URL(this.jobForm.webhookUrl);
        } catch {
          this.jobFormErrors.webhookUrl = "Invalid URL format";
          isValid = false;
        }
      }

      return isValid;
    },
    runJob() {
      if (!this.validateForm()) return;

      // Show warning for destructive actions
      if (this.jobForm.postProcessing === "delete") {
        this.showDestructiveWarning = true;
        return;
      }

      this.confirmRunJob();
    },
    async confirmRunJob() {
      this.showDestructiveWarning = false;
      this.jobRunning = true;
      this.jobStatus = null;
      this.jobProgress = 0;
      
      const taskAction = "run-one-time-job";
      const eventId = this.getUuid();

      this.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.runJobAborted
      );

      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.runJobCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            ...this.jobForm,
          },
          extra: {
            title: this.$t("action." + taskAction),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.jobRunning = false;
        this.createErrorNotificationForApp(
          err,
          this.$t("mail_webhooks.error_running_job")
        );
        return;
      }

      // Start polling for job status
      this.startJobStatusPolling(eventId);
    },
    runJobAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.jobRunning = false;
      this.jobStatus = {
        status: "failed",
        error: taskResult.error || "Job was aborted",
        details: this.jobForm,
      };
      this.stopJobStatusPolling();
    },
    runJobCompleted(taskContext, taskResult) {
      this.jobRunning = false;
      this.jobStatus = {
        status: "completed",
        details: {
          ...this.jobForm,
          emailsProcessed: taskResult.output.emailsProcessed,
          startTime: taskResult.output.startTime,
          endTime: taskResult.output.endTime,
        },
        logs: taskResult.output.logs || [],
      };
      this.jobProgress = 100;
      this.stopJobStatusPolling();
      this.createSuccessNotificationForApp(this.$t("mail_webhooks.job_started"));
    },
    startJobStatusPolling(jobId) {
      // Poll every 2 seconds for job progress
      this.jobStatusPollingInterval = setInterval(async () => {
        await this.pollJobStatus(jobId);
      }, 2000);
    },
    stopJobStatusPolling() {
      if (this.jobStatusPollingInterval) {
        clearInterval(this.jobStatusPollingInterval);
        this.jobStatusPollingInterval = null;
      }
    },
    async pollJobStatus(jobId) {
      // This would call an API to get the current job status
      // For now, we'll simulate progress
      if (this.jobRunning && this.jobProgress < 90) {
        this.jobProgress += 10;
        this.jobProgressLabel = `Processing emails... ${this.jobProgress}%`;
      }
    },
    formatDateTime(timestamp) {
      if (!timestamp) return "";
      return new Date(timestamp).toLocaleString();
    },
    formatTime(timestamp) {
      if (!timestamp) return "";
      return new Date(timestamp).toLocaleTimeString();
    },
  },
};
</script>

<style scoped lang="scss">
@import "@/styles/carbon-utils";

.one-time-job {
  padding: 1rem 0;
}

.description-section {
  margin-bottom: 1rem;
  
  p {
    color: #6f6f6f;
    margin: 0;
  }
}

.job-form {
  margin-bottom: 1.5rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-actions {
  display: flex;
  justify-content: flex-start;
}

.job-status-section {
  margin-top: 1.5rem;
}

.job-status-content {
  .job-status-header {
    margin-bottom: 0.75rem;
    
    h4 {
      margin: 0 0 0.75rem 0;
    }
  }
  
  .job-progress {
    margin-bottom: 0.75rem;
  }
  
  .job-details {
    margin-bottom: 0.75rem;
    
    p {
      margin: 0.5rem 0;
    }
  }
  
  .job-error {
    margin-bottom: 0.75rem;
    color: #da1e28;
    
    p {
      margin: 0;
    }
  }
  
  .job-logs {
    h5 {
      margin: 0 0 0.75rem 0;
    }
    
    .logs-container {
      background: #f4f4f4;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      padding: 0.75rem;
      max-height: 200px;
      overflow-y: auto;
      font-family: monospace;
      font-size: 12px;
      
      .log-entry {
        margin-bottom: 0.5rem;
        
        .log-timestamp {
          color: #8d8d8d;
          margin-right: 0.75rem;
        }
        
        .log-message {
          color: #161616;
        }
        
        &.error {
          .log-message {
            color: #da1e28;
          }
        }
        
        &.warning {
          .log-message {
            color: #f1c21b;
          }
        }
        
        &.info {
          .log-message {
            color: #0f62fe;
          }
        }
      }
    }
  }
}

.job-status-running {
  border-left: 4px solid #0f62fe;
}

.job-status-success {
  border-left: 4px solid #24a148;
}

.job-status-error {
  border-left: 4px solid #da1e28;
}
</style>
