<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("webhooks.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.listWebhooks">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('error.error')"
          :description="error.listWebhooks"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <div class="webhooks-header">
            <cv-button
              kind="primary"
              @click="showCreateModal = true"
              :disabled="loading.listWebhooks"
            >
              {{ $t("webhooks.create_webhook") }}
            </cv-button>
          </div>

          <!-- Webhooks Table -->
          <cv-data-table
            v-if="!loading.listWebhooks && webhooks.length > 0"
            :columns="columns"
            :data="webhooks"
            :sortable="true"
            :searchable="true"
            :searchPlaceholder="$t('common.search')"
            ref="webhooksTable"
          >
            <template slot="data" slot-scope="{ row }">
              <cv-data-table-row :key="row.id">
                <cv-data-table-cell>{{ row.name }}</cv-data-table-cell>
                <cv-data-table-cell>{{ row.url }}</cv-data-table-cell>
                <cv-data-table-cell>
                  <cv-tag
                    :kind="row.payload_type === 'JSON' ? 'blue' : 'gray'"
                    :label="
                      $t(
                        'webhooks.' + row.payload_type.toLowerCase() + '_format'
                      )
                    "
                  />
                </cv-data-table-cell>
                <cv-data-table-cell>
                  <cv-tag
                    :kind="row.trigger_type === 'realtime' ? 'green' : 'purple'"
                    :label="$t('webhooks.' + row.trigger_type)"
                  />
                </cv-data-table-cell>
                <cv-data-table-cell>
                  <cv-tag
                    :kind="row.active ? 'green' : 'red'"
                    :label="
                      row.active ? $t('common.enabled') : $t('common.disabled')
                    "
                  />
                </cv-data-table-cell>
                <cv-data-table-cell>{{
                  formatDate(row.last_triggered)
                }}</cv-data-table-cell>
                <cv-data-table-cell>
                  <cv-overflow-menu>
                    <cv-overflow-menu-option @click="testWebhook(row)">
                      {{ $t("webhooks.test_webhook") }}
                    </cv-overflow-menu-option>
                    <cv-overflow-menu-option @click="editWebhook(row)">
                      {{ $t("common.edit") }}
                    </cv-overflow-menu-option>
                    <cv-overflow-menu-option
                      danger
                      @click="confirmDeleteWebhook(row)"
                    >
                      {{ $t("webhooks.delete_webhook") }}
                    </cv-overflow-menu-option>
                  </cv-overflow-menu>
                </cv-data-table-cell>
              </cv-data-table-row>
            </template>
          </cv-data-table>
          <!-- Empty State -->
          <NsEmptyState
            v-else-if="!loading.listWebhooks && webhooks.length === 0"
            :title="$t('webhooks.no_webhooks')"
            :description="$t('webhooks.no_webhooks_description')"
          >
            <template #action>
              <cv-button kind="primary" @click="showCreateModal = true">
                {{ $t("webhooks.create_webhook") }}
              </cv-button>
            </template>
          </NsEmptyState>

          <!-- Loading State -->
          <cv-skeleton-text
            v-else-if="loading.listWebhooks"
            :paragraph="true"
            :line-count="3"
          ></cv-skeleton-text>
        </cv-tile>
      </cv-column>
    </cv-row>

    <!-- Create/Edit Webhook Modal -->
    <cv-modal
      :visible="showCreateModal || showEditModal"
      :primary-button-text="
        editingWebhook ? $t('common.save') : $t('common.create')
      "
      :secondary-button-text="$t('common.cancel')"
      @primary-click="saveWebhook"
      @secondary-click="closeModal"
      @modal-hidden="closeModal"
      :primary-button-disabled="loading.createWebhook || loading.updateWebhook"
      size="large"
    >
      <template slot="title">
        {{
          editingWebhook
            ? $t("webhooks.edit_webhook")
            : $t("webhooks.create_webhook")
        }}
      </template>
      <template slot="content">
        <WebhookForm
          ref="webhookForm"
          :webhook="currentWebhook"
          :loading="loading.createWebhook || loading.updateWebhook"
          @input="currentWebhook = $event"
        />
      </template>
    </cv-modal>

    <!-- Delete Confirmation Modal -->
    <NsModal
      kind="danger"
      :visible="showDeleteModal"
      :primary-button-text="$t('common.delete')"
      :secondary-button-text="$t('common.cancel')"
      @primary-click="deleteWebhook"
      @modal-hidden="showDeleteModal = false"
      :primary-button-disabled="loading.deleteWebhook"
    >
      <template slot="title">{{ $t("webhooks.delete_webhook") }}</template>
      <template slot="content">
        <p>{{ $t("webhooks.confirm_delete") }}</p>
        <p>
          <strong>{{ webhookToDelete && webhookToDelete.name }}</strong>
        </p>
      </template>
    </NsModal>

    <!-- Test Result Modal -->
    <NsModal
      :visible="showTestModal"
      :primary-button-text="$t('common.close')"
      @primary-click="showTestModal = false"
      @modal-hidden="showTestModal = false"
      :show-secondary-button="false"
    >
      <template slot="title">{{ $t("webhooks.test_webhook") }}</template>
      <template slot="content">
        <div v-if="testResult">
          <div class="test-result-status">
            <cv-tag
              :kind="testResult.success ? 'green' : 'red'"
              :label="
                testResult.success
                  ? $t('webhooks.test_success')
                  : $t('webhooks.test_failed')
              "
            />
            <span class="test-status-code"
              >{{ $t("common.status_code") }}:
              {{ testResult.status_code }}</span
            >
            <span class="test-response-time"
              >{{ $t("common.response_time") }}:
              {{ testResult.response_time }}s</span
            >
          </div>
          <div v-if="testResult.response_body" class="test-response">
            <h5>{{ $t("common.response") }}:</h5>
            <pre>{{ testResult.response_body }}</pre>
          </div>
          <div v-if="testResult.error" class="test-error">
            <h5>{{ $t("error.error") }}:</h5>
            <p>{{ testResult.error }}</p>
          </div>
        </div>
      </template>
    </NsModal>
  </cv-grid>
</template>

<script>
import {
  QueryParamService,
  TaskService,
  UtilService,
  NsEmptyState,
  NsModal,
  NsInlineNotification,
} from "@nethserver/ns8-ui-lib";
import WebhookForm from "../components/WebhookForm.vue";
import to from "await-to-js";
import { mapState } from "vuex";

export default {
  name: "Webhooks",
  components: {
    WebhookForm,
    NsEmptyState,
    NsModal,
    NsInlineNotification,
  },
  mixins: [QueryParamService, TaskService, UtilService],
  data() {
    return {
      webhooks: [],
      showCreateModal: false,
      showEditModal: false,
      showDeleteModal: false,
      showTestModal: false,
      editingWebhook: null,
      webhookToDelete: null,
      testResult: null,
      currentWebhook: {
        name: "",
        url: "",
        api_key: "",
        payload_type: "JSON",
        trigger_type: "realtime",
        interval: 300,
        mailboxes: [],
        filters: {},
        active: true,
      },
      columns: [
        { key: "name", label: this.$t("webhooks.webhook_name") },
        { key: "url", label: this.$t("webhooks.webhook_url") },
        { key: "payload_type", label: this.$t("webhooks.payload_type") },
        { key: "trigger_type", label: this.$t("webhooks.trigger_type") },
        { key: "active", label: this.$t("webhooks.active") },
        { key: "last_triggered", label: this.$t("webhooks.last_triggered") },
        { key: "actions", label: this.$t("common.actions") },
      ],
      loading: {
        listWebhooks: false,
        createWebhook: false,
        updateWebhook: false,
        deleteWebhook: false,
        testWebhook: false,
      },
      error: {
        listWebhooks: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
  },
  created() {
    this.listWebhooks();
  },
  methods: {
    async listWebhooks() {
      this.loading.listWebhooks = true;
      this.error.listWebhooks = "";

      const taskAction = "list-webhooks";
      const eventId = this.getUuid();

      // register to task error
      this.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.listWebhooksAborted
      );

      // register to task completion
      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.listWebhooksCompleted
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
        this.error.listWebhooks = this.getErrorMessage(err);
        this.loading.listWebhooks = false;
        return;
      }
    },
    listWebhooksAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.listWebhooks = this.$t("error.generic_error");
      this.loading.listWebhooks = false;
    },
    listWebhooksCompleted(taskContext, taskResult) {
      this.loading.listWebhooks = false;
      const output = taskResult.output;

      if (taskResult.exit_code !== 0) {
        console.error(`${taskContext.action} failed`, taskResult);
        this.error.listWebhooks = this.getErrorMessage(taskResult);
        return;
      }

      this.webhooks = output.webhooks || [];
    },
    editWebhook(webhook) {
      this.editingWebhook = webhook;
      this.currentWebhook = { ...webhook };
      this.showEditModal = true;
    },
    confirmDeleteWebhook(webhook) {
      this.webhookToDelete = webhook;
      this.showDeleteModal = true;
    },
    async saveWebhook() {
      // Validate form first
      if (this.$refs.webhookForm && !this.$refs.webhookForm.validate()) {
        return;
      }

      if (this.editingWebhook) {
        await this.updateWebhook();
      } else {
        await this.createWebhook();
      }
    },
    async createWebhook() {
      this.loading.createWebhook = true;

      const taskAction = "create-webhook";
      const eventId = this.getUuid();

      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.createWebhookCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: this.currentWebhook,
          extra: {
            title: this.$t("action." + taskAction),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.loading.createWebhook = false;
        return;
      }
    },
    createWebhookCompleted(taskContext, taskResult) {
      this.loading.createWebhook = false;

      if (taskResult.exit_code !== 0) {
        console.error(`${taskContext.action} failed`, taskResult);
        return;
      }

      this.closeModal();
      this.listWebhooks();
      this.createNotificationSuccess(this.$t("webhooks.webhook_created"));
    },
    async updateWebhook() {
      this.loading.updateWebhook = true;

      const taskAction = "update-webhook";
      const eventId = this.getUuid();

      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.updateWebhookCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            id: this.editingWebhook.id,
            ...this.currentWebhook,
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
        this.loading.updateWebhook = false;
        return;
      }
    },
    updateWebhookCompleted(taskContext, taskResult) {
      this.loading.updateWebhook = false;

      if (taskResult.exit_code !== 0) {
        console.error(`${taskContext.action} failed`, taskResult);
        return;
      }

      this.closeModal();
      this.listWebhooks();
      this.createNotificationSuccess(this.$t("webhooks.webhook_updated"));
    },
    async deleteWebhook() {
      this.loading.deleteWebhook = true;

      const taskAction = "delete-webhook";
      const eventId = this.getUuid();

      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.deleteWebhookCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            id: this.webhookToDelete.id,
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
        this.loading.deleteWebhook = false;
        return;
      }
    },
    deleteWebhookCompleted(taskContext, taskResult) {
      this.loading.deleteWebhook = false;

      if (taskResult.exit_code !== 0) {
        console.error(`${taskContext.action} failed`, taskResult);
        return;
      }

      this.showDeleteModal = false;
      this.webhookToDelete = null;
      this.listWebhooks();
      this.createNotificationSuccess(this.$t("webhooks.webhook_deleted"));
    },
    async testWebhook(webhook) {
      this.loading.testWebhook = true;

      const taskAction = "test-webhook";
      const eventId = this.getUuid();

      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.testWebhookCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            id: webhook.id,
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
        this.loading.testWebhook = false;
        return;
      }
    },
    testWebhookCompleted(taskContext, taskResult) {
      this.loading.testWebhook = false;

      if (taskResult.exit_code !== 0) {
        console.error(`${taskContext.action} failed`, taskResult);
        return;
      }

      this.testResult = taskResult.output;
      this.showTestModal = true;
    },
    closeModal() {
      this.showCreateModal = false;
      this.showEditModal = false;
      this.editingWebhook = null;
      this.currentWebhook = {
        name: "",
        url: "",
        api_key: "",
        payload_type: "JSON",
        trigger_type: "realtime",
        interval: 300,
        mailboxes: [],
        filters: {},
        active: true,
      };
    },
    formatDate(dateString) {
      if (!dateString) return this.$t("webhooks.never");
      return new Date(dateString).toLocaleString();
    },
  },
};
</script>

<style scoped lang="scss">
.webhooks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.test-result-status {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
}

.test-response,
.test-error {
  margin-top: 1rem;
}

.test-response pre {
  background-color: #f4f4f4;
  padding: 1rem;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}
</style>
