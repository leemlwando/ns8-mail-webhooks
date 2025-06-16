<!--
Copyright (C) 2023 Lee M. Lwando <leemlwando@gmail.com>
SPDX-License-Identifier: MIT
-->
<template>
  <cv-grid class="tab-content">
    <cv-row>
      <cv-column :lg="8">
        <div class="tab-description">
          <p>{{ $t("webhooks.one_time_job_description") }}</p>
        </div>
        
        <cv-form @submit.prevent="runJob">
          <cv-form-item>
            <cv-select
              :label="$t('webhooks.mailbox_to_process')"
              v-model="job.mailbox_to_process"
              :disabled="mailboxesLoading"
              :invalid="errors.mailbox_to_process"
              :invalid-message="errors.mailbox_to_process"
            >
              <cv-select-option disabled selected hidden value="">
                {{ $t("webhooks.choose_mailbox") }}
              </cv-select-option>
              <cv-select-option
                v-for="mailbox in mailboxes"
                :key="mailbox.address"
                :value="mailbox.address"
              >
                {{ mailbox.address }}
              </cv-select-option>
            </cv-select>
          </cv-form-item>

          <cv-text-input
            :label="$t('webhooks.webhook_url')"
            v-model.trim="job.webhook_url"
            :placeholder="$t('webhooks.webhook_url_placeholder')"
            class="form-item"
            :invalid="errors.webhook_url"
            :invalid-message="errors.webhook_url"
          />

          <cv-text-input
            :label="$t('webhooks.api_key_optional')"
            v-model.trim="job.api_key"
            password
            class="form-item"
            :placeholder="$t('webhooks.api_key_placeholder')"
          />

          <cv-form-group 
            :legend-text="$t('webhooks.payload_format')" 
            class="form-item"
          >
            <cv-radio-group v-model="job.payload_format">
              <cv-radio-button label="RAW" value="RAW" />
              <cv-radio-button label="JSON" value="JSON" />
            </cv-radio-group>
          </cv-form-group>

          <cv-form-group 
            :legend-text="$t('webhooks.after_processing')" 
            class="form-item"
          >
            <cv-radio-group v-model="job.post_scrape_action">
              <cv-radio-button 
                :label="$t('webhooks.mark_as_read')" 
                value="mark_as_read" 
              />
              <cv-radio-button 
                :label="$t('webhooks.delete_emails')" 
                value="delete" 
              />
            </cv-radio-group>
          </cv-form-group>

          <div class="action-section">
            <cv-button
              type="submit"
              :disabled="!isJobFormValid || jobRunning"
              kind="primary"
            >
              {{ $t("webhooks.run_now") }}
            </cv-button>

            <cv-inline-loading
              v-if="jobRunning"
              :loading-text="jobStatus"
              class="job-status-loader"
            />
          </div>
          
          <cv-inline-notification
            v-if="jobResult.message"
            :kind="jobResult.kind"
            :title="jobResult.title"
            :sub-title="jobResult.message"
            @close="jobResult.message = ''"
            class="job-status-notification"
          />
        </cv-form>
      </cv-column>
    </cv-row>
  </cv-grid>
</template>

<script>
import { UtilService } from "@/mixins/util";

export default {
  name: "OneTimeJob",
  mixins: [UtilService],
  data() {
    return {
      mailboxes: [],
      mailboxesLoading: false,
      jobRunning: false,
      jobStatus: "",
      jobResult: {
        kind: "",
        title: "",
        message: ""
      },
      job: {
        mailbox_to_process: "",
        webhook_url: "",
        api_key: "",
        payload_format: "RAW",
        post_scrape_action: "mark_as_read",
      },
      errors: {},
    };
  },
  computed: {
    isJobFormValid() {
      return (
        this.job.mailbox_to_process && 
        this.job.webhook_url &&
        this.isValidEmail(this.job.mailbox_to_process) &&
        this.isValidUrl(this.job.webhook_url)
      );
    },
  },
  methods: {
    async fetchMailboxes() {
      this.mailboxesLoading = true;
      try {
        // Mock data for now - in real implementation, this would call ns8-mail API
        this.mailboxes = [
          { address: "hr@example.com" },
          { address: "sales@example.com" },
          { address: "support@example.com" },
          { address: "admin@example.com" },
        ];
      } catch (error) {
        this.createErrorNotification(
          error,
          this.$t("error.cannot_fetch_mailboxes")
        );
      } finally {
        this.mailboxesLoading = false;
      }
    },
    
    validateJobForm() {
      this.errors = {};
      
      if (!this.job.mailbox_to_process) {
        this.errors.mailbox_to_process = this.$t("common.required_field");
      }
      
      if (!this.job.webhook_url) {
        this.errors.webhook_url = this.$t("common.required_field");
      } else if (!this.isValidUrl(this.job.webhook_url)) {
        this.errors.webhook_url = this.$t("error.invalid_url");
      }
      
      return Object.keys(this.errors).length === 0;
    },
    
    async runJob() {
      if (!this.validateJobForm()) {
        return;
      }
      
      this.jobRunning = true;
      this.jobStatus = this.$t("webhooks.processing");
      this.jobResult.message = ""; // Clear previous results

      try {
        const response = await this.axios.post("/api/actions/run-now", this.job);
        
        this.jobResult = {
          kind: "success",
          title: this.$t("webhooks.job_complete"),
          message: this.$t("webhooks.emails_processed", { 
            count: response.data.processed_count 
          })
        };
      } catch (error) {
        this.jobResult = {
          kind: "error",
          title: this.$t("webhooks.job_failed"),
          message: error.response?.data?.detail || error.message,
        };
      } finally {
        this.jobRunning = false;
      }
    },
  },
  created() {
    this.fetchMailboxes();
  },
};
</script>

<style lang="scss" scoped>
.tab-content {
  padding-top: 2rem;
}

.tab-description {
  margin-bottom: 1.5rem;
  
  p {
    color: var(--cds-text-02);
    font-size: 0.875rem;
    line-height: 1.4;
  }
}

.form-item {
  margin-bottom: 1.5rem;
}

.action-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.job-status-loader {
  margin-left: 1rem;
}

.job-status-notification {
  margin-top: 1.5rem;
}
</style>
