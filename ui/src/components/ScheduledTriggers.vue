<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <div class="scheduled-triggers">
    <div class="description-section">
      <p>{{ $t("mail_webhooks.scheduled_triggers_description") }}</p>
    </div>

    <cv-button
      kind="primary"
      @click="showAddModal = true"
      :disabled="loading.mailboxes"
    >
      {{ $t("mail_webhooks.add_scheduled_trigger") }}
    </cv-button>

    <div class="triggers-table-section">
      <cv-data-table
        v-if="triggers.length > 0"
        :columns="tableColumns"
        :data="formattedTriggers"
        :loading="componentLoading.triggers"
      >
        <template v-slot:cell:is_active="{ cell, row }">
          <cv-toggle
            :value="cell.value"
            @change="toggleTriggerStatus(row)"
            :disabled="componentLoading.toggleStatus"
            small
          >
            <template v-slot:text-left>{{ $t("common.inactive") }}</template>
            <template v-slot:text-right>{{ $t("common.active") }}</template>
          </cv-toggle>
        </template>
        
        <template v-slot:cell:actions="{ row }">
          <cv-overflow-menu>
            <cv-overflow-menu-item @click="editTrigger(row)">
              {{ $t("common.edit") }}
            </cv-overflow-menu-item>
            <cv-overflow-menu-item @click="deleteTrigger(row)" danger>
              {{ $t("common.delete") }}
            </cv-overflow-menu-item>
          </cv-overflow-menu>
        </template>
      </cv-data-table>

      <cv-tile v-else-if="!componentLoading.triggers" class="empty-state">
        <div class="empty-state-content">
          <h4>{{ $t("mail_webhooks.no_scheduled_triggers") }}</h4>
          <p>{{ $t("mail_webhooks.scheduled_triggers_description") }}</p>
          <cv-button
            kind="primary"
            @click="showAddModal = true"
            :disabled="loading.mailboxes"
          >
            {{ $t("mail_webhooks.add_scheduled_trigger") }}
          </cv-button>
        </div>
      </cv-tile>
    </div>

    <!-- Add/Edit Trigger Modal -->
    <cv-modal
      :visible="showAddModal || showEditModal"
      @modal-hide-request="closeModal"        :primary-button-disabled="!isFormValid || componentLoading.saveOperation"
      size="default"
    >
      <template v-slot:title>
        {{ showEditModal ? $t("mail_webhooks.edit_scheduled_trigger") : $t("mail_webhooks.add_scheduled_trigger") }}
      </template>
      
      <template v-slot:content>
        <cv-form @submit.prevent="saveTrigger">
          <cv-dropdown
            v-model="triggerForm.mailbox"
            :label="$t('mail_webhooks.mailbox')"
            :placeholder="$t('mail_webhooks.select_mailbox')"
            :disabled="loading.mailboxes"
            :invalid="triggerFormErrors.mailbox"
            :invalid-message="triggerFormErrors.mailbox"
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
            v-model="triggerForm.webhookUrl"
            :label="$t('mail_webhooks.webhook_url')"
            :placeholder="$t('mail_webhooks.webhook_url_placeholder')"
            :invalid="triggerFormErrors.webhookUrl"
            :invalid-message="triggerFormErrors.webhookUrl"
          />

          <cv-text-input
            v-model="triggerForm.apiKey"
            :label="$t('mail_webhooks.api_key_optional')"
            :placeholder="$t('mail_webhooks.api_key_placeholder')"
            type="password"
          />

          <cv-dropdown
            v-model="triggerForm.payloadFormat"
            :label="$t('mail_webhooks.payload_format')"
          >
            <cv-dropdown-item value="raw">
              {{ $t("mail_webhooks.payload_format_raw") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="json">
              {{ $t("mail_webhooks.payload_format_json") }}
            </cv-dropdown-item>
          </cv-dropdown>

          <cv-dropdown
            v-model="triggerForm.schedule"
            :label="$t('mail_webhooks.schedule')"
          >
            <cv-dropdown-item value="*/1 * * * *">
              {{ $t("mail_webhooks.schedule_every_minute") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="*/5 * * * *">
              {{ $t("mail_webhooks.schedule_every_5_minutes") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="*/15 * * * *">
              {{ $t("mail_webhooks.schedule_every_15_minutes") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="*/30 * * * *">
              {{ $t("mail_webhooks.schedule_every_30_minutes") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="0 * * * *">
              {{ $t("mail_webhooks.schedule_every_hour") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="0 */6 * * *">
              {{ $t("mail_webhooks.schedule_every_6_hours") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="0 */12 * * *">
              {{ $t("mail_webhooks.schedule_every_12_hours") }}
            </cv-dropdown-item>
            <cv-dropdown-item value="0 0 * * *">
              {{ $t("mail_webhooks.schedule_daily") }}
            </cv-dropdown-item>
          </cv-dropdown>
        </cv-form>
      </template>

      <template v-slot:secondary-button>{{ $t("common.cancel") }}</template>
      <template v-slot:primary-button>{{ $t("common.save") }}</template>
      
      <template v-slot:primary-button-action>
        <cv-button
          kind="primary"
          @click="saveTrigger"
          :disabled="!isFormValid"
          :loading="componentLoading.saveOperation"
        >
          {{ $t("common.save") }}
        </cv-button>
      </template>
    </cv-modal>

    <!-- Delete Confirmation Modal -->
    <cv-modal
      :visible="showDeleteModal"
      @modal-hide-request="showDeleteModal = false"
      kind="danger"
      size="small"
    >
      <template v-slot:title>{{ $t("mail_webhooks.delete_scheduled_trigger") }}</template>
      <template v-slot:content>
        <p>{{ $t("mail_webhooks.confirm_delete") }}</p>
      </template>
      <template v-slot:secondary-button>{{ $t("common.cancel") }}</template>
      <template v-slot:primary-button>{{ $t("common.delete") }}</template>
      <template v-slot:primary-button-action>
        <cv-button
          kind="danger"
          @click="confirmDeleteTrigger"
          :loading="componentLoading.deleteOperation"
        >
          {{ $t("common.delete") }}
        </cv-button>
      </template>
    </cv-modal>
  </div>
</template>

<script>
import { UtilService, TaskService } from "@nethserver/ns8-ui-lib";
import to from "await-to-js";

export default {
  name: "ScheduledTriggers",
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
      triggers: [],
      showAddModal: false,
      showEditModal: false,
      showDeleteModal: false,      editingTrigger: null,
      deletingTrigger: null,
      triggerForm: this.getEmptyTriggerForm(),
      triggerFormErrors: {},
      componentLoading: {
        triggers: true,
        saveOperation: false,
        deleteOperation: false,
        toggleStatus: false,
      },
      tableColumns: [
        { key: "mailbox", header: this.$t("mail_webhooks.mailbox") },
        { key: "webhookUrl", header: this.$t("mail_webhooks.webhook_url") },
        { key: "schedule", header: this.$t("mail_webhooks.schedule") },
        { key: "status", header: this.$t("mail_webhooks.status") },
        { key: "lastRun", header: this.$t("mail_webhooks.last_run") },
        { key: "nextRun", header: this.$t("mail_webhooks.next_run") },
        { key: "actions", header: this.$t("common.actions") },
      ],
    };  },
  computed: {
    isFormValid() {
      return (
        this.triggerForm.name &&
        this.triggerForm.mailbox &&
        this.triggerForm.webhook_url &&
        this.triggerForm.payload_format &&
        this.validateForm()
      );
    },
    formattedTriggers() {
      return this.triggers.map(trigger => ({
        ...trigger,
        // Format the data for display
        actions: 'actions', // placeholder for actions column
      }));
    },
  },
  created() {
    this.loadTriggers();
  },
  methods: {
    getEmptyTriggerForm() {
      return {
        name: "",
        mailbox: "",
        webhook_url: "",
        api_key: "",
        payload_format: "RAW",
        is_active: true,
      };
    },
    validateForm() {
      this.triggerFormErrors = {};
      let isValid = true;

      if (!this.triggerForm.name) {
        this.triggerFormErrors.name = this.$t("common.required");
        isValid = false;
      }

      if (!this.triggerForm.mailbox) {
        this.triggerFormErrors.mailbox = this.$t("common.required");
        isValid = false;
      }

      if (!this.triggerForm.webhook_url) {
        this.triggerFormErrors.webhook_url = this.$t("common.required");
        isValid = false;
      } else {
        try {
          new URL(this.triggerForm.webhook_url);
        } catch {
          this.triggerFormErrors.webhook_url = "Invalid URL format";
          isValid = false;
        }
      }

      return isValid;
    },
    async loadTriggers() {
      this.componentLoading.triggers = true;
      
      try {
        const response = await fetch('/api/configs');
        const data = await response.json();
        this.triggers = data.configs || [];
      } catch (error) {
        console.error('Failed to load triggers:', error);
        this.createErrorNotificationForApp(
          error,
          this.$t("Failed to load scheduled triggers")
        );
      } finally {
        this.componentLoading.triggers = false;
      }
    },
    closeModal() {
      this.showAddModal = false;
      this.showEditModal = false;
      this.editingTrigger = null;
      this.triggerForm = this.getEmptyTriggerForm();
      this.triggerFormErrors = {};
    },
    editTrigger(trigger) {
      this.editingTrigger = trigger;
      this.triggerForm = { ...trigger };
      this.showEditModal = true;
    },
    deleteTrigger(trigger) {
      this.deletingTrigger = trigger;
      this.showDeleteModal = true;
    },
    async saveTrigger() {
      if (!this.validateForm()) return;

      this.componentLoading.saveOperation = true;
      
      try {
        const response = await fetch('/api/configs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(this.triggerForm),
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        this.createSuccessNotificationForApp(
          this.$t("Scheduled trigger saved successfully")
        );
        
        this.closeModal();
        await this.loadTriggers();
        
      } catch (error) {
        console.error('Failed to save trigger:', error);
        this.createErrorNotificationForApp(
          error,
          this.$t("Failed to save scheduled trigger")
        );
      } finally {
        this.componentLoading.saveOperation = false;
      }
    },
    async toggleTriggerStatus(trigger) {
      this.componentLoading.toggleStatus = true;
      
      try {
        const updatedTrigger = {
          ...trigger,
          is_active: !trigger.is_active
        };
        
        const response = await fetch('/api/configs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updatedTrigger),
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        await this.loadTriggers();
        
      } catch (error) {
        console.error('Failed to toggle trigger status:', error);
        this.createErrorNotificationForApp(
          error,
          this.$t("Failed to update trigger status")
        );
      } finally {
        this.componentLoading.toggleStatus = false;
      }
    },
    async confirmDelete() {
      this.componentLoading.deleteOperation = true;
      
      try {
        const response = await fetch(`/api/configs/${this.deletingTrigger.id}`, {
          method: 'DELETE',
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        this.createSuccessNotificationForApp(
          this.$t("Scheduled trigger deleted successfully")
        );
        
        this.showDeleteModal = false;
        this.deletingTrigger = null;
        await this.loadTriggers();
        
      } catch (error) {
        console.error('Failed to delete trigger:', error);
        this.createErrorNotificationForApp(
          error,
          this.$t("Failed to delete scheduled trigger")
        );      } finally {
        this.componentLoading.deleteOperation = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
@import "@/styles/carbon-utils";

.scheduled-triggers {
  padding: 1rem 0;
}

.description-section {
  margin-bottom: 1rem;

  p {
    color: #6f6f6f;
    margin: 0;
  }
}

.triggers-table-section {
  margin-top: 1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;

  .empty-state-content {
    h4 {
      margin-bottom: 0.75rem;
    }

    p {
      color: #6f6f6f;
      margin-bottom: 1rem;
    }
  }
}
</style>
