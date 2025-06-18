<!--
  Copyright (C) 2025 Nethesis S.r.l.
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
          :title="$t('webhooks.list_webhooks')"
          :description="error.listWebhooks"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <div class="webhook-actions mg-bottom">
            <NsButton
              kind="primary"
              :icon="Add20"
              @click="showCreateWebhookModal = true"
              :disabled="loading.listWebhooks"
            >
              {{ $t("webhooks.create_webhook") }}
            </NsButton>
            <NsButton
              kind="secondary"
              :icon="Refresh20"
              @click="listWebhooks"
              :loading="loading.listWebhooks"
            >
              {{ $t("common.refresh") }}
            </NsButton>
          </div>
          
          <cv-data-table
            :columns="webhookColumns"
            :data="webhooks"
            :loading="loading.listWebhooks"
            @sort="onSort"
          >
            <template v-slot:data>
              <cv-data-table-row
                v-for="(webhook, index) in webhooks"
                :key="webhook.id"
              >
                <cv-data-table-cell>{{ webhook.name }}</cv-data-table-cell>
                <cv-data-table-cell>{{ webhook.url }}</cv-data-table-cell>
                <cv-data-table-cell>{{ webhook.payload_type }}</cv-data-table-cell>
                <cv-data-table-cell>{{ webhook.trigger_type }}</cv-data-table-cell>
                <cv-data-table-cell>
                  <cv-tag
                    :kind="webhook.active ? 'green' : 'red'"
                    :label="webhook.active ? $t('common.active') : $t('common.inactive')"
                  />
                </cv-data-table-cell>
                <cv-data-table-cell>
                  {{ formatDate(webhook.created_at) }}
                </cv-data-table-cell>
                <cv-data-table-cell>
                  {{ webhook.last_triggered ? formatDate(webhook.last_triggered) : $t('common.never') }}
                </cv-data-table-cell>
                <cv-data-table-cell>
                  <cv-overflow-menu tip-position="left" tip-alignment="end">
                    <cv-overflow-menu-item @click="testWebhook(webhook)">
                      <NsMenuItem :icon="Play20" :label="$t('webhooks.test_webhook')" />
                    </cv-overflow-menu-item>
                    <cv-overflow-menu-item @click="editWebhook(webhook)">
                      <NsMenuItem :icon="Edit20" :label="$t('webhooks.edit_webhook')" />
                    </cv-overflow-menu-item>
                    <cv-overflow-menu-item @click="deleteWebhook(webhook)">
                      <NsMenuItem :icon="TrashCan20" :label="$t('webhooks.delete_webhook')" />
                    </cv-overflow-menu-item>
                  </cv-overflow-menu>
                </cv-data-table-cell>
              </cv-data-table-row>
            </template>
            <template v-slot:empty-state>
              <cv-tile>
                <NsEmptyState :title="$t('webhooks.no_webhooks')">
                  <template #description>
                    {{ $t('webhooks.no_webhooks_description') }}
                  </template>
                  <template #action>
                    <NsButton
                      kind="primary"
                      :icon="Add20"
                      @click="showCreateWebhookModal = true"
                    >
                      {{ $t("webhooks.create_webhook") }}
                    </NsButton>
                  </template>
                </NsEmptyState>
              </cv-tile>
            </template>
          </cv-data-table>
        </cv-tile>
      </cv-column>
    </cv-row>

    <!-- Create/Edit Webhook Modal -->
    <NsModal
      size="default"
      :visible="showCreateWebhookModal || showEditWebhookModal"
      @modal-hidden="onModalHidden"
      @primary-click="saveWebhook"
      @secondary-click="onModalHidden"
      :primary-button-disabled="loading.createWebhook"
      :secondary-button-disabled="loading.createWebhook"
    >
      <template slot="title">{{
        showEditWebhookModal
          ? $t("webhooks.edit_webhook")
          : $t("webhooks.create_webhook")
      }}</template>
      <template slot="content">
        <cv-form @submit.prevent="saveWebhook">
          <cv-text-input
            :label="$t('webhooks.webhook_name')"
            v-model="webhookForm.name"
            :disabled="loading.createWebhook"
            :invalid-message="error.webhookForm.name"
            ref="webhookName"
          />
          
          <cv-text-input
            :label="$t('webhooks.webhook_url')"
            v-model="webhookForm.url"
            :disabled="loading.createWebhook"
            :invalid-message="error.webhookForm.url"
            ref="webhookUrl"
          />
          
          <cv-text-input
            :label="$t('webhooks.api_key')"
            type="password"
            v-model="webhookForm.api_key"
            :disabled="loading.createWebhook"
            :invalid-message="error.webhookForm.api_key"
            ref="webhookApiKey"
          />
          
          <cv-dropdown
            :label="$t('webhooks.payload_type')"
            v-model="webhookForm.payload_type"
            :disabled="loading.createWebhook"
          >
            <cv-dropdown-item value="JSON">JSON</cv-dropdown-item>
            <cv-dropdown-item value="RAW">RAW</cv-dropdown-item>
          </cv-dropdown>
          
          <cv-dropdown
            :label="$t('webhooks.trigger_type')"
            v-model="webhookForm.trigger_type"
            :disabled="loading.createWebhook"
          >
            <cv-dropdown-item value="realtime">{{ $t('webhooks.realtime') }}</cv-dropdown-item>
            <cv-dropdown-item value="interval">{{ $t('webhooks.interval') }}</cv-dropdown-item>
          </cv-dropdown>
          
          <cv-text-input
            v-if="webhookForm.trigger_type === 'interval'"
            :label="$t('webhooks.interval_seconds')"
            type="number"
            v-model="webhookForm.interval"
            :disabled="loading.createWebhook"
            :invalid-message="error.webhookForm.interval"
            ref="webhookInterval"
          />
          
          <cv-toggle
            value="active"
            :label="$t('webhooks.active')"
            v-model="webhookForm.active"
            :disabled="loading.createWebhook"
          />
        </cv-form>
      </template>
      <template slot="secondary-button">{{ $t("common.cancel") }}</template>
      <template slot="primary-button">{{
        showEditWebhookModal ? $t("common.save") : $t("common.create")
      }}</template>
    </NsModal>
  </cv-grid>
</template>

<script>
import to from "await-to-js";
import { mapState } from "vuex";
import {
  QueryParamService,
  UtilService,
  TaskService,
  IconService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";

export default {
  name: "Webhooks",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    PageTitleService,
  ],
  pageTitle() {
    return this.$t("webhooks.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "webhooks",
      },
      urlCheckInterval: null,
      webhooks: [],
      showCreateWebhookModal: false,
      showEditWebhookModal: false,
      editingWebhook: null,
      webhookForm: {
        name: "",
        url: "",
        api_key: "",
        payload_type: "JSON",
        trigger_type: "realtime",
        interval: 60,
        active: true,
      },
      webhookColumns: [
        {
          key: "name",
          label: this.$t("webhooks.webhook_name"),
          sortable: true,
        },
        {
          key: "url",
          label: this.$t("webhooks.webhook_url"),
          sortable: true,
        },
        {
          key: "payload_type",
          label: this.$t("webhooks.payload_type"),
          sortable: true,
        },
        {
          key: "trigger_type",
          label: this.$t("webhooks.trigger_type"),
          sortable: true,
        },
        {
          key: "active",
          label: this.$t("common.status"),
          sortable: true,
        },
        {
          key: "created_at",
          label: this.$t("webhooks.created_at"),
          sortable: true,
        },
        {
          key: "last_triggered",
          label: this.$t("webhooks.last_triggered"),
          sortable: true,
        },
        {
          key: "actions",
          label: "",
        },
      ],
      loading: {
        listWebhooks: false,
        createWebhook: false,
      },
      error: {
        listWebhooks: "",
        webhookForm: {
          name: "",
          url: "",
          api_key: "",
          interval: "",
        },
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.watchQueryData(vm);
      vm.urlCheckInterval = vm.initUrlBindingForApp(vm, vm.q.page);
    });
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.urlCheckInterval);
    next();
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
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.listWebhooksAborted
      );

      // register to task completion
      this.core.$root.$once(
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
      this.webhooks = taskResult.output || [];
    },
    resetWebhookForm() {
      this.webhookForm = {
        name: "",
        url: "",
        api_key: "",
        payload_type: "JSON",
        trigger_type: "realtime",
        interval: 60,
        active: true,
      };
      this.clearErrors(this);
    },
    onModalHidden() {
      this.showCreateWebhookModal = false;
      this.showEditWebhookModal = false;
      this.editingWebhook = null;
      this.resetWebhookForm();
    },
    editWebhook(webhook) {
      this.editingWebhook = webhook;
      this.webhookForm = { ...webhook };
      this.showEditWebhookModal = true;
      this.focusElement("webhookName");
    },
    async saveWebhook() {
      if (!this.validateWebhookForm()) {
        return;
      }

      this.loading.createWebhook = true;
      const taskAction = this.showEditWebhookModal ? "update-webhook" : "create-webhook";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.saveWebhookAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.saveWebhookCompleted
      );

      const taskData = { ...this.webhookForm };
      if (this.showEditWebhookModal && this.editingWebhook) {
        taskData.id = this.editingWebhook.id;
      }

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: taskData,
          extra: {
            title: this.$t("webhooks." + taskAction.replace("-", "_")),
            description: this.$t("common.processing"),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.createWebhook = this.getErrorMessage(err);
        this.loading.createWebhook = false;
        return;
      }
    },
    saveWebhookAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.createWebhook = this.$t("error.generic_error");
      this.loading.createWebhook = false;
    },
    saveWebhookCompleted() {
      this.loading.createWebhook = false;
      this.onModalHidden();
      this.listWebhooks(); // Refresh the list
    },
    validateWebhookForm() {
      this.clearErrors(this);
      let isValidationOk = true;

      if (!this.webhookForm.name) {
        this.error.webhookForm.name = this.$t("common.required");
        if (isValidationOk) {
          this.focusElement("webhookName");
          isValidationOk = false;
        }
      }

      if (!this.webhookForm.url) {
        this.error.webhookForm.url = this.$t("common.required");
        if (isValidationOk) {
          this.focusElement("webhookUrl");
          isValidationOk = false;
        }
      }

      return isValidationOk;
    },
    async testWebhook(webhook) {
      // Implementation for testing webhook
      console.log("Testing webhook:", webhook);
    },
    async deleteWebhook(webhook) {
      // Implementation for deleting webhook
      console.log("Deleting webhook:", webhook);
    },
    formatDate(dateString) {
      if (!dateString) return "";
      return new Date(dateString).toLocaleString();
    },
    onSort(sortData) {
      // Implementation for sorting
      console.log("Sort data:", sortData);
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.webhook-actions {
  display: flex;
  gap: $spacing-05;
  margin-bottom: $spacing-06;
}

.mg-bottom {
  margin-bottom: $spacing-06;
}
</style>
