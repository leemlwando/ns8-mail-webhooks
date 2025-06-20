<!--
  Copyright (C) 2025 Lee M. Lwando
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <div>
    <cv-grid fullWidth>
      <cv-row>
        <cv-column class="page-title">
          <h2>{{ $t("webhooks.title") }}</h2>
        </cv-column>
      </cv-row>
      <cv-row class="toolbar">
        <cv-column>
          <NsButton
            kind="secondary"
            :icon="Add20"
            @click="showCreateWebhookModal"
            :disabled="loading.listWebhooks"
            >{{ $t("webhooks.create_webhook") }}
          </NsButton>
        </cv-column>
      </cv-row>
      <cv-row v-if="error.listWebhooks">
        <cv-column>
          <NsInlineNotification
            kind="error"
            :title="$t('action.list-webhooks')"
            :description="error.listWebhooks"
            :showCloseButton="false"
          />
        </cv-column>
      </cv-row>
      <cv-row>
        <cv-column>
          <cv-tile light v-if="loading.listWebhooks">
            <cv-skeleton-text
              :paragraph="true"
              :line-count="6"
            ></cv-skeleton-text>
          </cv-tile>
          <cv-tile light v-else-if="!webhooks.length">
            <NsEmptyState :title="$t('webhooks.no_webhooks')">
              <template #description>
                {{ $t("webhooks.no_webhooks_description") }}
              </template>
            </NsEmptyState>
          </cv-tile>
          <NsDataTable
            v-else
            :allRows="webhooks"
            :columns="i18nTableColumns"
            :rawColumns="tableColumns"
            :pageSizes="[10, 25, 50, 100]"
            :overflow-menu="true"
            isSearchable
            :searchPlaceholder="$t('webhooks.search_webhook')"
            :searchClearLabel="core.$t('common.clear_search')"
            :noSearchResultsLabel="core.$t('common.no_search_results')"
            :noSearchResultsDescription="
              core.$t('common.no_search_results_description')
            "
            :isLoading="loading.listWebhooks"
            :skeletonRows="5"
            :isErrorShown="!!error.listWebhooks"
            :errorTitle="$t('action.list-webhooks')"
            :errorDescription="error.listWebhooks"
            :itemsPerPageLabel="core.$t('pagination.items_per_page')"
            :rangeOfTotalItemsLabel="core.$t('pagination.range_of_total_items')"
            :ofTotalPagesLabel="core.$t('pagination.of_total_pages')"
            :backwardText="core.$t('pagination.previous_page')"
            :forwardText="core.$t('pagination.next_page')"
            :pageNumberLabel="core.$t('pagination.page_number')"
            :label="$t('webhooks.webhooks_table_label')"
            @updatePage="tablePage = $event"
          >
            <template slot="empty-state">
              <NsEmptyState :title="$t('webhooks.no_webhooks')">
                <template #description>
                  {{ $t("webhooks.no_webhooks_description") }}
                </template>
              </NsEmptyState>
            </template>
            <template slot="data">
              <cv-data-table-row
                v-for="(row, rowIndex) in tablePage"
                :key="`${rowIndex}`"
                :value="`${rowIndex}`"
                class="table-row"
              >
                <cv-data-table-cell :title="$t('webhooks.toggle_status')" class="toggle-cell">
                  <cv-toggle
                    :value="row.enabled"
                    @change="(newValue) => toggleWebhook(row, newValue)"
                    :disabled="loading.toggleWebhook"
                    size="sm"
                    :title="
                      row.enabled
                        ? $t('webhooks.click_to_disable')
                        : $t('webhooks.click_to_enable')
                    "
                  >
                    <template slot="text-left">{{
                      $t("webhooks.disabled")
                    }}</template>
                    <template slot="text-right">{{
                      $t("webhooks.enabled")
                    }}</template>
                  </cv-toggle>
                </cv-data-table-cell>
                <cv-data-table-cell :title="row.email">
                  {{ row.email }}
                </cv-data-table-cell>
                <cv-data-table-cell class="url-cell" :title="row.url">
                  <NsButton
                    kind="ghost"
                    size="sm"
                    :icon="Launch20"
                    @click="openUrl(row.url)"
                    class="url-button"
                    :title="$t('webhooks.open_url', { url: row.url })"
                  >
                    {{ truncateUrl(row.url) }}
                  </NsButton>
                </cv-data-table-cell>
                <cv-data-table-cell
                  :title="
                    $t(`webhooks.post_action_${row.post_action}_description`)
                  "
                >
                  <cv-tag
                    :kind="getPostActionKind(row.post_action)"
                    :label="$t(`webhooks.post_action_${row.post_action}`)"
                  ></cv-tag>
                </cv-data-table-cell>
                <cv-data-table-cell
                  :title="
                    $t(`webhooks.payload_type_${row.payload_type}_description`)
                  "
                >
                  <cv-tag
                    :kind="row.payload_type === 'json' ? 'blue' : 'purple'"
                    :label="row.payload_type.toUpperCase()"
                  ></cv-tag>
                </cv-data-table-cell>
                <cv-data-table-cell
                  :title="
                    row.last_run
                      ? formatDate(row.last_run)
                      : $t('webhooks.never_run')
                  "
                >
                  <span v-if="row.last_run">
                    {{ formatDate(row.last_run) }}
                  </span>
                  <span v-else class="text-muted">
                    {{ $t("webhooks.never_run") }}
                  </span>
                </cv-data-table-cell>
                <cv-data-table-cell :title="getNextRunTitle(row)">
                  <span v-if="row.is_realtime">
                    <cv-tag
                      kind="green"
                      :label="$t('webhooks.realtime')"
                      size="sm"
                    ></cv-tag>
                  </span>
                  <span v-else-if="row.next_run && row.enabled">
                    {{ formatDate(row.next_run) }}
                  </span>
                  <span v-else-if="!row.enabled" class="text-muted">
                    {{ $t("webhooks.disabled") }}
                  </span>
                  <span v-else class="text-muted">
                    {{ $t("webhooks.not_scheduled") }}
                  </span>
                </cv-data-table-cell>
                <cv-data-table-cell
                  :title="
                    $t('webhooks.run_count_description', {
                      count: row.run_count || 0,
                    })
                  "
                >
                  {{ row.run_count || 0 }}
                </cv-data-table-cell>
                <cv-data-table-cell class="table-overflow-menu-cell">
                  <div class="action-buttons">
                    <NsButton
                      kind="ghost"
                      size="sm"
                      :icon="Play20"
                      @click="triggerWebhook(row)"
                      :disabled="loading.triggerWebhook || !row.enabled"
                      :title="$t('webhooks.run_now')"
                    />
                    <cv-overflow-menu
                      :flip-menu="true"
                      tip-position="left"
                      tip-alignment="center"
                      class="table-overflow-menu"
                    >
                      <cv-overflow-menu-item @click="showEditWebhookModal(row)">
                        <NsMenuItem :icon="Edit20" :label="$t('common.edit')" />
                      </cv-overflow-menu-item>
                      <NsMenuDivider />
                      <cv-overflow-menu-item
                        danger
                        @click="showDeleteWebhookModal(row)"
                      >
                        <NsMenuItem
                          :icon="TrashCan20"
                          :label="$t('common.delete')"
                        />
                      </cv-overflow-menu-item>
                    </cv-overflow-menu>
                  </div>
                </cv-data-table-cell>
              </cv-data-table-row>
            </template>
          </NsDataTable>
        </cv-column>
      </cv-row>
    </cv-grid>

    <!-- Create/Edit Webhook Modal -->
    <CreateOrEditWebhookModal
      :isShown="isCreateOrEditWebhookModalShown"
      :webhook="currentWebhook"
      :isEditing="isEditingWebhook"
      @hide="hideCreateOrEditWebhookModal"
      @webhookCreated="webhookCreated"
      @webhookEdited="webhookEdited"
    />

    <!-- Delete Webhook Modal -->
    <NsDangerDeleteModal
      :isShown="isDeleteWebhookModalShown"
      :name="webhookToDelete ? webhookToDelete.email : ''"
      :title="$t('webhooks.delete_webhook')"
      :warning="$t('webhooks.delete_webhook_warning')"
      :description="$t('webhooks.delete_webhook_description')"
      :typeToConfirm="$t('common.delete')"
      @hide="hideDeleteWebhookModal"
      @confirmDelete="deleteWebhook"
    />
  </div>
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
import CreateOrEditWebhookModal from "@/components/CreateOrEditWebhookModal";

export default {
  name: "Webhooks",
  components: {
    CreateOrEditWebhookModal,
  },
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
      webhooks: [],
      tablePage: [],
      isCreateOrEditWebhookModalShown: false,
      isDeleteWebhookModalShown: false,
      currentWebhook: null,
      isEditingWebhook: false,
      webhookToDelete: null,
      loading: {
        listWebhooks: false,
        toggleWebhook: false,
        triggerWebhook: false,
        deleteWebhook: false,
      },
      error: {
        listWebhooks: "",
        toggleWebhook: "",
        triggerWebhook: "",
        deleteWebhook: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
    tableColumns() {
      return [
        "enabled",
        "email",
        "url",
        "post_action",
        "payload_type",
        "last_run",
        "next_run",
        "run_count",
        "menu",
      ];
    },
    i18nTableColumns() {
      return this.tableColumns.map((column) => {
        return this.$t("webhooks." + column);
      });
    },
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.watchQueryData(vm);
      vm.urlCheckInterval = vm.initUrlBindingForApp(vm, vm.q.page);
    });
  },
  beforeRouteUpdate(to, from, next) {
    this.watchQueryData(this);
    next();
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.urlCheckInterval);
    next();
  },
  mounted() {
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
        // Error creating task - log for debugging
        this.error.listWebhooks = this.getErrorMessage(err);
        this.loading.listWebhooks = false;
        return;
      }
    },
    listWebhooksAborted() {
      // Task aborted - handle error
      this.error.listWebhooks = this.$t("error.generic_error");
      this.loading.listWebhooks = false;
    },
    listWebhooksCompleted(taskContext, taskResult) {
      this.loading.listWebhooks = false;
      this.webhooks = taskResult.output;
    },
    showCreateWebhookModal() {
      this.currentWebhook = null;
      this.isEditingWebhook = false;
      this.isCreateOrEditWebhookModalShown = true;
    },
    showEditWebhookModal(webhook) {
      this.currentWebhook = webhook;
      this.isEditingWebhook = true;
      this.isCreateOrEditWebhookModalShown = true;
    },
    hideCreateOrEditWebhookModal() {
      this.isCreateOrEditWebhookModalShown = false;
    },
    showDeleteWebhookModal(webhook) {
      this.webhookToDelete = webhook;
      this.isDeleteWebhookModalShown = true;
    },
    hideDeleteWebhookModal() {
      this.isDeleteWebhookModalShown = false;
      this.webhookToDelete = null;
    },
    async deleteWebhook() {
      this.loading.deleteWebhook = true;
      this.error.deleteWebhook = "";
      const taskAction = "remove-webhook";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.deleteWebhookAborted
      );

      // register to task completion
      this.core.$root.$once(
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
            description: this.$t("webhooks.deleting_webhook", {
              email: this.webhookToDelete.email,
            }),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        // Error creating task - log for debugging
        this.error.deleteWebhook = this.getErrorMessage(err);
        this.loading.deleteWebhook = false;
        return;
      }
      this.hideDeleteWebhookModal();
    },
    deleteWebhookAborted() {
      // Task aborted - handle error
      this.error.deleteWebhook = this.$t("error.generic_error");
      this.loading.deleteWebhook = false;
    },
    deleteWebhookCompleted() {
      this.loading.deleteWebhook = false;
      // Refresh the list
      this.listWebhooks();
    },
    async toggleWebhook(webhook, newEnabled) {
      this.loading.toggleWebhook = true;
      this.error.toggleWebhook = "";
      const taskAction = "edit-webhook";
      const eventId = this.getUuid();

      // Only send fields allowed by the schema
      const updatedWebhook = {
        id: webhook.id,
        email: webhook.email,
        url: webhook.url,
        enabled: newEnabled,
        post_action: webhook.post_action,
        payload_type: webhook.payload_type,
      };

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.toggleWebhookAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.toggleWebhookCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: updatedWebhook,
          extra: {
            title: this.$t("action." + taskAction),
            description: this.$t("webhooks.toggling_webhook", {
              email: webhook.email,
            }),
            isNotificationHidden: true,
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        // Error creating task - log for debugging
        this.error.toggleWebhook = this.getErrorMessage(err);
        this.loading.toggleWebhook = false;
        return;
      }
    },
    toggleWebhookAborted() {
      // Task aborted - handle error
      this.error.toggleWebhook = this.$t("error.generic_error");
      this.loading.toggleWebhook = false;
    },
    toggleWebhookCompleted(taskContext, taskResult) {
      this.loading.toggleWebhook = false;
      // Update webhook in list
      const index = this.webhooks.findIndex(
        (w) => w.id === taskResult.output.id
      );
      if (index !== -1) {
        this.$set(this.webhooks, index, taskResult.output);
      }
    },
    async triggerWebhook(webhook) {
      this.loading.triggerWebhook = true;
      this.error.triggerWebhook = "";
      const taskAction = "trigger-webhook";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.triggerWebhookAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.triggerWebhookCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            id: webhook.id,
          },
          extra: {
            title: this.$t("action." + taskAction),
            description: this.$t("webhooks.triggering_webhook", {
              email: webhook.email,
            }),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        // Error creating task - log for debugging
        this.error.triggerWebhook = this.getErrorMessage(err);
        this.loading.triggerWebhook = false;
        return;
      }
    },
    triggerWebhookAborted() {
      // Task aborted - handle error
      this.error.triggerWebhook = this.$t("error.generic_error");
      this.loading.triggerWebhook = false;
    },
    triggerWebhookCompleted(taskResult) {
      this.loading.triggerWebhook = false;
      // Show success notification
      this.createNotificationSuccess({
        title: this.$t("webhooks.webhook_triggered"),
        description: this.$t("webhooks.webhook_triggered_description", {
          status: taskResult.output.response_status,
        }),
      });
      // Refresh the list to update trigger count
      this.listWebhooks();
    },
    webhookCreated() {
      this.hideCreateOrEditWebhookModal();
      this.listWebhooks();
    },
    webhookEdited() {
      this.hideCreateOrEditWebhookModal();
      this.listWebhooks();
    },
    truncateUrl(url) {
      if (url.length > 40) {
        return url.substring(0, 37) + "...";
      }
      return url;
    },
    openUrl(url) {
      window.open(url, "_blank");
    },
    getPostActionKind(action) {
      switch (action) {
        case "none":
          return "gray";
        case "mark_as_read":
          return "blue";
        case "delete":
          return "red";
        default:
          return "gray";
      }
    },
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleString();
    },
    getNextRunTitle(row) {
      if (row.is_realtime) {
        return this.$t("webhooks.realtime_description");
      } else if (row.next_run && row.enabled) {
        return this.$t("webhooks.next_run_at", {
          time: this.formatDate(row.next_run),
        });
      } else if (!row.enabled) {
        return this.$t("webhooks.webhook_disabled");
      } else {
        return this.$t("webhooks.not_scheduled_description");
      }
    },
  },
};
</script>

<style scoped>
.toolbar {
  margin-bottom: 1rem;
}

.url-cell {
  max-width: 200px;
}

.url-button {
  text-align: left;
  justify-content: flex-start;
  padding: 0.25rem 0.5rem;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.text-muted {
  color: #6f6f6f;
  font-style: italic;
}

.custom-interval-result {
  margin-top: 0.25rem;
}

.toggle-cell {
  padding: 0.75rem 1rem;
  min-width: 120px;
  width: 120px;
}

.toggle-cell .bx--toggle {
  margin: 0;
  vertical-align: middle;
}

.toggle-cell .bx--toggle__switch {
  margin-right: 0.5rem;
}
</style>
