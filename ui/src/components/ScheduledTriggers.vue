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
        :data="triggers"
        :loading="loading.triggers"
      >
        <template v-slot:cell:status="{ cell, row }">
          <cv-toggle
            :value="cell.value === 'active'"
            @change="toggleTriggerStatus(row)"
            :disabled="loading.toggleStatus"
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

      <cv-tile v-else-if="!loading.triggers" class="empty-state">
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
      @modal-hide-request="closeModal"
      :primary-button-disabled="!isFormValid || loading.saveOperation"
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
          :loading="loading.saveOperation"
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
          :loading="loading.deleteOperation"
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
      showDeleteModal: false,
      editingTrigger: null,
      deletingTrigger: null,
      triggerForm: this.getEmptyTriggerForm(),
      triggerFormErrors: {},
      loading: {
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
    };
  },
  computed: {
    isFormValid() {
      return (
        this.triggerForm.mailbox &&
        this.triggerForm.webhookUrl &&
        this.triggerForm.payloadFormat &&
        this.triggerForm.schedule &&
        this.validateForm()
      );
    },
  },
  created() {
    this.loadTriggers();
  },
  methods: {
    getEmptyTriggerForm() {
      return {
        mailbox: "",
        webhookUrl: "",
        apiKey: "",
        payloadFormat: "json",
        schedule: "*/15 * * * *",
      };
    },
    validateForm() {
      this.triggerFormErrors = {};
      let isValid = true;

      if (!this.triggerForm.mailbox) {
        this.triggerFormErrors.mailbox = this.$t("common.required");
        isValid = false;
      }

      if (!this.triggerForm.webhookUrl) {
        this.triggerFormErrors.webhookUrl = this.$t("common.required");
        isValid = false;
      } else {
        try {
          new URL(this.triggerForm.webhookUrl);
        } catch {
          this.triggerFormErrors.webhookUrl = "Invalid URL format";
          isValid = false;
        }
      }

      return isValid;
    },
    async loadTriggers() {
      this.loading.triggers = true;
      
      const taskAction = "get-scheduled-triggers";
      const eventId = this.getUuid();

      this.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.loadTriggersAborted
      );

      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.loadTriggersCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          extra: {
            title: this.$t("action." + taskAction),
            isNotificationHidden: true,
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.loading.triggers = false;
        return;
      }
    },
    loadTriggersAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.loading.triggers = false;
    },
    loadTriggersCompleted(taskContext, taskResult) {
      this.triggers = taskResult.output.triggers || [];
      this.loading.triggers = false;
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

      this.loading.saveOperation = true;
      
      const taskAction = this.showEditModal ? "update-scheduled-trigger" : "create-scheduled-trigger";
      const eventId = this.getUuid();
      
      const data = {
        ...this.triggerForm,
      };
      
      if (this.showEditModal) {
        data.id = this.editingTrigger.id;
      }

      this.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.saveTriggerAborted
      );

      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.saveTriggerCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data,
          extra: {
            title: this.$t("action." + taskAction),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.loading.saveOperation = false;
        return;
      }
    },
    saveTriggerAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.loading.saveOperation = false;
    },
    saveTriggerCompleted() {
      this.loading.saveOperation = false;
      this.closeModal();
      this.loadTriggers();
      this.createSuccessNotificationForApp(this.$t("mail_webhooks.trigger_saved"));
    },
    async confirmDeleteTrigger() {
      this.loading.deleteOperation = true;
      
      const taskAction = "delete-scheduled-trigger";
      const eventId = this.getUuid();

      this.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.deleteTriggerAborted
      );

      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.deleteTriggerCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: { id: this.deletingTrigger.id },
          extra: {
            title: this.$t("action." + taskAction),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.loading.deleteOperation = false;
        return;
      }
    },
    deleteTriggerAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.loading.deleteOperation = false;
    },
    deleteTriggerCompleted() {
      this.loading.deleteOperation = false;
      this.showDeleteModal = false;
      this.deletingTrigger = null;
      this.loadTriggers();
      this.createSuccessNotificationForApp(this.$t("mail_webhooks.trigger_deleted"));
    },
    async toggleTriggerStatus(trigger) {
      this.loading.toggleStatus = true;
      
      const newStatus = trigger.status === "active" ? "inactive" : "active";
      const taskAction = "update-scheduled-trigger";
      const eventId = this.getUuid();

      this.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.toggleStatusAborted
      );

      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.toggleStatusCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: { 
            id: trigger.id,
            status: newStatus,
          },
          extra: {
            title: this.$t("action." + taskAction),
            isNotificationHidden: true,
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.loading.toggleStatus = false;
        return;
      }
    },
    toggleStatusAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.loading.toggleStatus = false;
    },
    toggleStatusCompleted() {
      this.loading.toggleStatus = false;
      this.loadTriggers();
    },
  },
};
</script>

<style scoped lang="scss">
.scheduled-triggers {
  padding: $spacing-05 0;
}

.description-section {
  margin-bottom: $spacing-05;
  
  p {
    color: $text-02;
    margin: 0;
  }
}

.triggers-table-section {
  margin-top: $spacing-05;
}

.empty-state {
  text-align: center;
  padding: $spacing-07;
  
  .empty-state-content {
    h4 {
      margin-bottom: $spacing-03;
    }
    
    p {
      color: $text-02;
      margin-bottom: $spacing-05;
    }
  }
}
</style>
