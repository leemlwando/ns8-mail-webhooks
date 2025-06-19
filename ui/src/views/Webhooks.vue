<!--
  Copyright (C) 2025 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("webhooks.title") }}</h2>
        <p>{{ $t("webhooks.description") }}</p>
      </cv-column>
    </cv-row>

    <!-- NS8 Mail Integration Status -->
    <cv-row v-if="mailIntegrationStatus">
      <cv-column>
        <cv-tile light>
          <h4>{{ $t("webhooks.mail_integration_status") }}</h4>
          <div v-if="mailIntegrationStatus.success" class="status-success">
            <CheckmarkFilled16 />
            <span>{{ $t("webhooks.ns8_mail_connected") }}</span>
            <p class="mg-top-sm">
              {{ $t("webhooks.mail_servers_found", {count: mailIntegrationStatus.details.mail_servers_found}) }}
              {{ $t("webhooks.addresses_available", {count: availableAddresses.length}) }}
            </p>
          </div>
          <div v-else class="status-error">
            <ErrorFilled16 />
            <span>{{ $t("webhooks.ns8_mail_disconnected") }}</span>
            <p class="mg-top-sm">{{ $t("webhooks.ns8_mail_required") }}</p>
          </div>
        </cv-tile>
      </cv-column>
    </cv-row>

    <!-- Create Webhook Button -->
    <cv-row v-if="mailIntegrationStatus && mailIntegrationStatus.success">
      <cv-column>
        <NsButton
          kind="primary"
          :icon="Add20"
          @click="showCreateWebhookModal = true"
          :disabled="loading.createWebhook"
        >
          {{ $t("webhooks.create_webhook") }}
        </NsButton>
      </cv-column>
    </cv-row>

    <!-- Webhooks List -->
    <cv-row>
      <cv-column>
        <cv-tile light>
          <h4>{{ $t("webhooks.existing_webhooks") }}</h4>
          
          <cv-data-table
            v-if="webhooks.length > 0"
            :columns="webhookTableColumns"
            :data="webhooks"
            :title="$t('webhooks.webhooks_table_title')"
          >
            <template v-slot:cell-active="{ cell }">
              <cv-toggle
                :value="cell.value"
                @change="toggleWebhookActive($event, cell.row)"
                :disabled="loading.toggleActive"
              />
            </template>
            <template v-slot:cell-actions="{ cell }">
              <cv-overflow-menu>
                <cv-overflow-menu-item @click="testWebhook(cell.row)">
                  {{ $t("webhooks.test") }}
                </cv-overflow-menu-item>
                <cv-overflow-menu-item @click="editWebhook(cell.row)">
                  {{ $t("webhooks.edit") }}
                </cv-overflow-menu-item>
                <cv-overflow-menu-item @click="deleteWebhook(cell.row)">
                  {{ $t("webhooks.delete") }}
                </cv-overflow-menu-item>
              </cv-overflow-menu>
            </template>
          </cv-data-table>
          
          <div v-else class="empty-state">
            <p>{{ $t("webhooks.no_webhooks") }}</p>
            <p class="mg-top-sm">{{ $t("webhooks.create_first_webhook") }}</p>
          </div>
        </cv-tile>
      </cv-column>
    </cv-row>

    <!-- Create/Edit Webhook Modal -->
    <cv-modal
      :visible="showCreateWebhookModal || showEditWebhookModal"
      :primary-button-text="isEditMode ? $t('webhooks.update') : $t('webhooks.create')"
      :secondary-button-text="$t('common.cancel')"
      size="large"
      @primary="submitWebhook"
      @secondary="closeWebhookModal"
      @modal-hide="closeWebhookModal"
    >
      <template v-slot:title>
        {{ isEditMode ? $t("webhooks.edit_webhook") : $t("webhooks.create_webhook") }}
      </template>
      
      <template v-slot:content>
        <cv-form @submit.prevent="submitWebhook">
          <cv-text-input
            :label="$t('webhooks.name')"
            v-model="webhookForm.name"
            :invalid-message="errors.name"
            required
          />
          
          <cv-text-input
            :label="$t('webhooks.url')"
            v-model="webhookForm.url"
            :invalid-message="errors.url"
            placeholder="https://your-server.com/webhook"
            required
          />
          
          <cv-text-input
            :label="$t('webhooks.api_key')"
            v-model="webhookForm.api_key"
            :placeholder="$t('webhooks.api_key_optional')"
          />

          <cv-dropdown
            :label="$t('webhooks.trigger_type')"
            v-model="webhookForm.trigger_config.trigger_type"
            :options="triggerTypeOptions"
            @change="onTriggerTypeChange"
          />

          <cv-text-input
            v-if="webhookForm.trigger_config.trigger_type === 'interval'"
            :label="$t('webhooks.interval_seconds')"
            v-model="webhookForm.trigger_config.interval_seconds"
            type="number"
            min="60"
            :placeholder="$t('webhooks.interval_placeholder')"
          />

          <cv-dropdown
            :label="$t('webhooks.payload_format')"
            v-model="webhookForm.payload_format"
            :options="payloadFormatOptions"
          />

          <cv-multi-select
            :label="$t('webhooks.email_addresses')"
            v-model="webhookForm.email_addresses"
            :options="emailAddressOptions"
            :placeholder="$t('webhooks.select_email_addresses')"
          />

          <cv-multi-select
            :label="$t('webhooks.mailboxes')"
            v-model="webhookForm.trigger_config.mailboxes"
            :options="mailboxOptions"
            :placeholder="$t('webhooks.select_mailboxes')"
          />

          <!-- Mail Filters -->
          <h5 class="mg-top">{{ $t("webhooks.mail_filters") }}</h5>
          
          <cv-text-input
            :label="$t('webhooks.sender_filter')"
            v-model="webhookForm.trigger_config.mail_filters.sender"
            :placeholder="$t('webhooks.sender_filter_placeholder')"
          />
          
          <cv-text-input
            :label="$t('webhooks.subject_filter')"
            v-model="webhookForm.trigger_config.mail_filters.subject"
            :placeholder="$t('webhooks.subject_filter_placeholder')"
          />
          
          <cv-text-input
            :label="$t('webhooks.body_filter')"
            v-model="webhookForm.trigger_config.mail_filters.body"
            :placeholder="$t('webhooks.body_filter_placeholder')"
          />
        </cv-form>
      </template>
    </cv-modal>

    <!-- Test Results Modal -->
    <cv-modal
      :visible="showTestResults"
      :primary-button-text="$t('common.close')"
      @primary="showTestResults = false"
      @modal-hide="showTestResults = false"
    >
      <template v-slot:title>
        {{ $t("webhooks.test_results") }}
      </template>
      
      <template v-slot:content>
        <div v-if="testResults">
          <div :class="testResults.success ? 'status-success' : 'status-error'">
            <component :is="testResults.success ? CheckmarkFilled16 : ErrorFilled16" />
            <span>{{ testResults.success ? $t('webhooks.test_success') : $t('webhooks.test_failed') }}</span>
          </div>
          
          <cv-structured-list class="mg-top">
            <template v-slot:items>
              <cv-structured-list-item>
                <cv-structured-list-data>{{ $t('webhooks.status_code') }}</cv-structured-list-data>
                <cv-structured-list-data>{{ testResults.status_code }}</cv-structured-list-data>
              </cv-structured-list-item>
              <cv-structured-list-item>
                <cv-structured-list-data>{{ $t('webhooks.response_time') }}</cv-structured-list-data>
                <cv-structured-list-data>{{ testResults.response_time }}ms</cv-structured-list-data>
              </cv-structured-list-item>
              <cv-structured-list-item v-if="testResults.error">
                <cv-structured-list-data>{{ $t('webhooks.error') }}</cv-structured-list-data>
                <cv-structured-list-data>{{ testResults.error }}</cv-structured-list-data>
              </cv-structured-list-item>
            </template>
          </cv-structured-list>
        </div>
      </template>
    </cv-modal>
  </cv-grid>
</template>

<script>
import {
  Add20,
  CheckmarkFilled16,
  ErrorFilled16,
} from "@carbon/icons-vue";

export default {
  name: "Webhooks",
  components: {
    Add20,
    CheckmarkFilled16,
    ErrorFilled16,
  },
  data() {
    return {
      webhooks: [],
      availableAddresses: [],
      mailIntegrationStatus: null,
      showCreateWebhookModal: false,
      showEditWebhookModal: false,
      showTestResults: false,
      testResults: null,
      loading: {
        createWebhook: false,
        editWebhook: false,
        toggleActive: false,
        deleteWebhook: false,
        testWebhook: false,
      },
      errors: {},
      webhookForm: {
        name: "",
        url: "",
        api_key: "",
        payload_format: "json",
        trigger_config: {
          trigger_type: "realtime",
          interval_seconds: 300,
          mailboxes: [],
          mail_filters: {
            sender: "",
            subject: "",
            body: "",
          },
        },
        email_addresses: [],
        headers: {},
        timeout: 30,
        active: true,
      },
      editingWebhook: null,
    };
  },
  computed: {
    isEditMode() {
      return !!this.editingWebhook;
    },
    webhookTableColumns() {
      return [
        { key: "name", label: this.$t("webhooks.name") },
        { key: "url", label: this.$t("webhooks.url") },
        { key: "trigger_config.trigger_type", label: this.$t("webhooks.trigger_type") },
        { key: "email_addresses", label: this.$t("webhooks.email_addresses") },
        { key: "active", label: this.$t("webhooks.active") },
        { key: "actions", label: this.$t("webhooks.actions") },
      ];
    },
    triggerTypeOptions() {
      return [
        { value: "realtime", label: this.$t("webhooks.realtime") },
        { value: "interval", label: this.$t("webhooks.interval") },
      ];
    },
    payloadFormatOptions() {
      return [
        { value: "json", label: this.$t("webhooks.json_format") },
        { value: "raw", label: this.$t("webhooks.raw_format") },
      ];
    },
    emailAddressOptions() {
      return this.availableAddresses.map(addr => ({
        value: addr.address || addr,
        label: addr.address || addr,
      }));
    },
    mailboxOptions() {
      return [
        { value: "INBOX", label: "INBOX" },
        ...this.availableAddresses.map(addr => ({
          value: addr.address || addr,
          label: addr.address || addr,
        })),
      ];
    },
  },
  async mounted() {
    await this.loadData();
  },
  methods: {
    async loadData() {
      await Promise.all([
        this.loadWebhooks(),
        this.loadAvailableAddresses(),
        this.testMailIntegration(),
      ]);
    },
    async loadWebhooks() {
      try {
        const response = await this.$http.get("/api/webhooks");
        this.webhooks = response.data;
      } catch (error) {
        console.error("Error loading webhooks:", error);
        this.$root.$emit("notification", {
          type: "error",
          message: this.$t("webhooks.error_loading_webhooks"),
        });
      }
    },
    async loadAvailableAddresses() {
      try {
        const response = await this.$http.get("/api/mail/addresses");
        this.availableAddresses = [
          ...response.data.addresses,
          ...response.data.mailboxes,
        ];
      } catch (error) {
        console.error("Error loading email addresses:", error);
        this.availableAddresses = [];
      }
    },
    async testMailIntegration() {
      try {
        const response = await this.$http.get("/api/mail/test");
        this.mailIntegrationStatus = response.data;
      } catch (error) {
        console.error("Error testing mail integration:", error);
        this.mailIntegrationStatus = {
          success: false,
          message: "Failed to test NS8 mail integration",
        };
      }
    },
    async submitWebhook() {
      try {
        this.errors = {};
        const isEdit = this.isEditMode;
        
        if (isEdit) {
          this.loading.editWebhook = true;
          await this.$http.put(`/api/webhooks/${this.editingWebhook.id}`, this.webhookForm);
        } else {
          this.loading.createWebhook = true;
          await this.$http.post("/api/webhooks", this.webhookForm);
        }
        
        this.$root.$emit("notification", {
          type: "success",
          message: this.$t(isEdit ? "webhooks.webhook_updated" : "webhooks.webhook_created"),
        });
        
        await this.loadWebhooks();
        this.closeWebhookModal();
      } catch (error) {
        console.error("Error submitting webhook:", error);
        if (error.response?.data?.detail) {
          this.$root.$emit("notification", {
            type: "error",
            message: error.response.data.detail,
          });
        }
      } finally {
        this.loading.createWebhook = false;
        this.loading.editWebhook = false;
      }
    },
    async toggleWebhookActive(active, webhook) {
      try {
        this.loading.toggleActive = true;
        await this.$http.put(`/api/webhooks/${webhook.id}`, { active });
        await this.loadWebhooks();
      } catch (error) {
        console.error("Error toggling webhook active status:", error);
        this.$root.$emit("notification", {
          type: "error",
          message: this.$t("webhooks.error_toggle_active"),
        });
      } finally {
        this.loading.toggleActive = false;
      }
    },
    async testWebhook(webhook) {
      try {
        this.loading.testWebhook = true;
        const response = await this.$http.post(`/api/webhooks/${webhook.id}/test`);
        this.testResults = response.data;
        this.showTestResults = true;
      } catch (error) {
        console.error("Error testing webhook:", error);
        this.$root.$emit("notification", {
          type: "error",
          message: this.$t("webhooks.error_testing_webhook"),
        });
      } finally {
        this.loading.testWebhook = false;
      }
    },
    editWebhook(webhook) {
      this.editingWebhook = webhook;
      this.webhookForm = { ...webhook };
      this.showEditWebhookModal = true;
    },
    async deleteWebhook(webhook) {
      if (confirm(this.$t("webhooks.confirm_delete"))) {
        try {
          this.loading.deleteWebhook = true;
          await this.$http.delete(`/api/webhooks/${webhook.id}`);
          this.$root.$emit("notification", {
            type: "success",
            message: this.$t("webhooks.webhook_deleted"),
          });
          await this.loadWebhooks();
        } catch (error) {
          console.error("Error deleting webhook:", error);
          this.$root.$emit("notification", {
            type: "error",
            message: this.$t("webhooks.error_deleting_webhook"),
          });
        } finally {
          this.loading.deleteWebhook = false;
        }
      }
    },
    closeWebhookModal() {
      this.showCreateWebhookModal = false;
      this.showEditWebhookModal = false;
      this.editingWebhook = null;
      this.webhookForm = {
        name: "",
        url: "",
        api_key: "",
        payload_format: "json",
        trigger_config: {
          trigger_type: "realtime",
          interval_seconds: 300,
          mailboxes: [],
          mail_filters: {
            sender: "",
            subject: "",
            body: "",
          },
        },
        email_addresses: [],
        headers: {},
        timeout: 30,
        active: true,
      };
      this.errors = {};
    },
    onTriggerTypeChange() {
      // Reset interval when changing trigger type
      if (this.webhookForm.trigger_config.trigger_type !== "interval") {
        this.webhookForm.trigger_config.interval_seconds = 300;
      }
    },
  },
};
</script>

<style scoped>
.status-success {
  display: flex;
  align-items: center;
  color: #24a148;
}

.status-error {
  display: flex;
  align-items: center;
  color: #da1e28;
}

.status-success svg,
.status-error svg {
  margin-right: 0.5rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6f6f6f;
}

.mg-top {
  margin-top: 1rem;
}

.mg-top-sm {
  margin-top: 0.5rem;
}
</style>
