<!--
  Copyright (C) 2025 Leemlwando
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <!-- Page Header -->
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("webhooks.title") }}</h2>
      </cv-column>
    </cv-row>

    <!-- Action Bar -->
    <cv-row class="action-bar">
      <cv-column>
        <NsButton
          kind="primary"
          :icon="Add20"
          @click="showCreateModal"
          :disabled="loading.getWebhooks"
          class="create-button"
        >
          {{ $t("webhooks.add_webhook") }}
        </NsButton>
      </cv-column>
    </cv-row>

    <!-- Error Display -->
    <cv-row v-if="error.getWebhooks">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-webhooks')"
          :description="error.getWebhooks"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>

    <!-- Webhooks Data Table -->
    <cv-row>
      <cv-column>
        <cv-data-table
          ref="webhooksTable"
          :columns="tableColumns"
          :data="webhooks"
          :loading="loading.getWebhooks"
          :pagination="true"
          :page-size="10"
          @sort="handleSort"
          class="webhooks-table"
        >
          <template slot="data">
            <cv-data-table-row
              v-for="(webhook, index) in paginatedWebhooks"
              :key="webhook.id"
              class="webhook-row"
            >
              <!-- Index Column -->
              <cv-data-table-cell class="index-cell">
                {{ getRowIndex(index) }}
              </cv-data-table-cell>

              <!-- Enabled Toggle Column -->
              <cv-data-table-cell class="toggle-cell">
                <cv-toggle
                  :value="webhook.enabled"
                  @change="toggleWebhookStatus(webhook)"
                  :disabled="loading.toggleWebhook"
                  :aria-label="
                    webhook.enabled
                      ? $t('webhooks.disable_webhook')
                      : $t('webhooks.enable_webhook')
                  "
                />
              </cv-data-table-cell>

              <!-- Name Column -->
              <cv-data-table-cell class="name-cell">
                <span class="webhook-name" :title="webhook.name">
                  {{ webhook.name }}
                </span>
              </cv-data-table-cell>

              <!-- URL Column -->
              <cv-data-table-cell class="url-cell">
                <span class="webhook-url" :title="webhook.url">
                  {{ truncateText(webhook.url, 40) }}
                </span>
              </cv-data-table-cell>

              <!-- Email Address Column -->
              <cv-data-table-cell class="email-cell">
                {{ webhook.email_address }}
              </cv-data-table-cell>

              <!-- Payload Type Column -->
              <cv-data-table-cell class="payload-cell">
                <cv-tag
                  :label="webhook.payload_type.toUpperCase()"
                  :kind="webhook.payload_type === 'json' ? 'blue' : 'gray'"
                />
              </cv-data-table-cell>

              <!-- Post Action Column -->
              <cv-data-table-cell class="action-cell">
                {{ formatPostAction(webhook.post_action) }}
              </cv-data-table-cell>

              <!-- Trigger Type Column -->
              <cv-data-table-cell class="trigger-cell">
                <cv-tag
                  :label="formatTriggerType(webhook.trigger_type)"
                  :kind="webhook.trigger_type === 'real time' ? 'green' : 'purple'"
                />
              </cv-data-table-cell>

              <!-- Last Run Column -->
              <cv-data-table-cell class="date-cell">
                <span class="date-text">
                  {{ formatDateTime(webhook.last_run) }}
                </span>
              </cv-data-table-cell>

              <!-- Next Run Column -->
              <cv-data-table-cell class="date-cell">
                <span class="date-text">
                  {{ formatDateTime(webhook.next_run) }}
                </span>
              </cv-data-table-cell>

              <!-- Actions Column -->
              <cv-data-table-cell class="actions-cell">
                <cv-overflow-menu
                  :flip-menu="true"
                  class="webhook-actions-menu"
                  :aria-label="$t('webhooks.webhook_actions')"
                >
                  <cv-overflow-menu-item @click="editWebhook(webhook)">
                    <NsMenuAction
                      :icon="Edit20"
                      :label="$t('common.edit')"
                    />
                  </cv-overflow-menu-item>
                  <cv-overflow-menu-item @click="deleteWebhook(webhook)">
                    <NsMenuAction
                      :icon="TrashCan20"
                      :label="$t('common.delete')"
                      kind="danger"
                    />
                  </cv-overflow-menu-item>
                </cv-overflow-menu>
              </cv-data-table-cell>
            </cv-data-table-row>
          </template>

          <!-- Empty State -->
          <template slot="empty-state">
            <NsEmptyState :title="$t('webhooks.no_webhooks')">
              <template #description>
                <div>{{ $t('webhooks.no_webhooks_description') }}</div>
                <NsButton
                  kind="ghost"
                  :icon="Add20"
                  @click="showCreateModal"
                  class="empty-state-button"
                >
                  {{ $t('webhooks.create_first_webhook') }}
                </NsButton>
              </template>
            </NsEmptyState>
          </template>
        </cv-data-table>
      </cv-column>
    </cv-row>

    <!-- Create/Edit Modal -->
    <WebhookModal
      :visible="isModalVisible"
      :webhook="selectedWebhook"
      :loading="loading.saveWebhook"
      :error="error.saveWebhook"
      @close="hideModal"
      @save="saveWebhook"
    />

    <!-- Delete Confirmation Modal -->
    <NsConfirmationModal
      :visible="isDeleteModalVisible"
      :title="$t('webhooks.delete_webhook')"
      :message="getDeleteConfirmationMessage()"
      :loading="loading.deleteWebhook"
      @confirm="confirmDeleteWebhook"
      @cancel="hideDeleteModal"
    />
  </cv-grid>
</template>

<script>
import { mapState } from "vuex";
import {
  QueryParamService,
  UtilService,
  TaskService,
  IconService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";
import WebhookModal from "@/components/WebhookModal.vue";

export default {
  name: "Webhooks",
  components: {
    WebhookModal,
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
      urlCheckInterval: null,
      webhooks: [],
      selectedWebhook: {},
      isModalVisible: false,
      isDeleteModalVisible: false,
      currentPage: 1,
      pageSize: 10,
      sortBy: null,
      sortDirection: "asc",
      tableColumns: [
        {
          label: this.$t("webhooks.index"),
          headingStyle: { width: "60px", textAlign: "center" },
        },
        {
          label: this.$t("webhooks.enabled"),
          headingStyle: { width: "80px", textAlign: "center" },
        },
        {
          label: this.$t("webhooks.name"),
          headingStyle: { width: "150px" },
        },
        {
          label: this.$t("webhooks.url"),
          headingStyle: { width: "200px" },
        },
        {
          label: this.$t("webhooks.email_address"),
          headingStyle: { width: "150px" },
        },
        {
          label: this.$t("webhooks.payload_type"),
          headingStyle: { width: "100px", textAlign: "center" },
        },
        {
          label: this.$t("webhooks.post_action"),
          headingStyle: { width: "120px" },
        },
        {
          label: this.$t("webhooks.trigger_type"),
          headingStyle: { width: "120px", textAlign: "center" },
        },
        {
          label: this.$t("webhooks.last_run"),
          headingStyle: { width: "130px" },
        },
        {
          label: this.$t("webhooks.next_run"),
          headingStyle: { width: "130px" },
        },
        {
          label: this.$t("common.actions"),
          headingStyle: { width: "80px", textAlign: "center" },
        },
      ],
      loading: {
        getWebhooks: false,
        saveWebhook: false,
        deleteWebhook: false,
        toggleWebhook: false,
      },
      error: {
        getWebhooks: "",
        saveWebhook: "",
        deleteWebhook: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
    paginatedWebhooks() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.sortedWebhooks.slice(start, end);
    },
    sortedWebhooks() {
      if (!this.sortBy) return this.webhooks;
      
      return [...this.webhooks].sort((a, b) => {
        const aVal = a[this.sortBy];
        const bVal = b[this.sortBy];
        
        if (this.sortDirection === "asc") {
          return aVal > bVal ? 1 : -1;
        } else {
          return aVal < bVal ? 1 : -1;
        }
      });
    },
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
    this.loadWebhooks();
  },
  methods: {
    async loadWebhooks() {
      this.loading.getWebhooks = true;
      this.error.getWebhooks = "";

      try {
        // Mock data for now - replace with actual API call
        await this.simulateApiCall(1000);
        
        this.webhooks = [
          {
            id: 1,
            name: "Order Notifications",
            url: "https://api.example.com/webhooks/orders",
            api_key: "secret123",
            email_address: "orders@example.com",
            payload_type: "json",
            post_action: "mark as read",
            trigger_type: "real time",
            enabled: true,
            last_run: "2025-06-21T10:30:00Z",
            next_run: null,
          },
          {
            id: 2,
            name: "Support Tickets",
            url: "https://support.example.com/webhook",
            api_key: "",
            email_address: "support@example.com",
            payload_type: "raw",
            post_action: "none",
            trigger_type: "scheduled",
            enabled: false,
            last_run: "2025-06-20T15:45:00Z",
            next_run: "2025-06-21T15:45:00Z",
          },
          {
            id: 3,
            name: "Marketing Updates",
            url: "https://marketing.example.com/api/emails",
            api_key: "mk_12345",
            email_address: "marketing@example.com",
            payload_type: "json",
            post_action: "delete",
            trigger_type: "scheduled",
            enabled: true,
            last_run: null,
            next_run: "2025-06-21T18:00:00Z",
          },
        ];
      } catch (error) {
        this.error.getWebhooks = this.getErrorMessage(error);
      } finally {
        this.loading.getWebhooks = false;
      }
    },

    showCreateModal() {
      this.selectedWebhook = {
        name: "",
        url: "",
        api_key: "",
        email_address: "",
        payload_type: "json",
        post_action: "none",
        trigger_type: "real time",
        enabled: true,
      };
      this.isModalVisible = true;
    },

    editWebhook(webhook) {
      this.selectedWebhook = { ...webhook };
      this.isModalVisible = true;
    },

    hideModal() {
      this.isModalVisible = false;
      this.selectedWebhook = {};
      this.error.saveWebhook = "";
    },

    async saveWebhook(webhook) {
      this.loading.saveWebhook = true;
      this.error.saveWebhook = "";

      try {
        // Mock save operation - replace with actual API call
        await this.simulateApiCall(1000);
        
        if (webhook.id) {
          // Update existing webhook
          const index = this.webhooks.findIndex((w) => w.id === webhook.id);
          if (index !== -1) {
            this.webhooks[index] = { ...webhook };
          }
        } else {
          // Create new webhook
          webhook.id = Date.now();
          this.webhooks.push(webhook);
        }

        this.hideModal();
      } catch (error) {
        this.error.saveWebhook = this.getErrorMessage(error);
      } finally {
        this.loading.saveWebhook = false;
      }
    },

    deleteWebhook(webhook) {
      this.selectedWebhook = webhook;
      this.isDeleteModalVisible = true;
    },

    hideDeleteModal() {
      this.isDeleteModalVisible = false;
      this.selectedWebhook = {};
    },

    async confirmDeleteWebhook() {
      this.loading.deleteWebhook = true;

      try {
        // Mock delete operation - replace with actual API call
        await this.simulateApiCall(500);
        
        this.webhooks = this.webhooks.filter(
          (w) => w.id !== this.selectedWebhook.id
        );
        
        this.hideDeleteModal();
      } catch (error) {
        this.error.deleteWebhook = this.getErrorMessage(error);
      } finally {
        this.loading.deleteWebhook = false;
      }
    },

    async toggleWebhookStatus(webhook) {
      this.loading.toggleWebhook = true;

      try {
        // Mock toggle operation - replace with actual API call
        await this.simulateApiCall(500);
        
        webhook.enabled = !webhook.enabled;
      } catch (error) {
        // Revert the change on error
        webhook.enabled = !webhook.enabled;
        this.error.getWebhooks = this.getErrorMessage(error);
      } finally {
        this.loading.toggleWebhook = false;
      }
    },

    handleSort(sortBy) {
      if (this.sortBy === sortBy.name) {
        this.sortDirection = this.sortDirection === "asc" ? "desc" : "asc";
      } else {
        this.sortBy = sortBy.name;
        this.sortDirection = "asc";
      }
    },

    formatDateTime(dateString) {
      if (!dateString) return "-";
      
      try {
        return new Date(dateString).toLocaleString(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        });
      } catch {
        return "-";
      }
    },

    formatPostAction(action) {
      const actionMap = {
        none: this.$t("webhooks.action_none"),
        "mark as read": this.$t("webhooks.action_mark_read"),
        delete: this.$t("webhooks.action_delete"),
      };
      return actionMap[action] || action;
    },

    formatTriggerType(type) {
      const typeMap = {
        "real time": this.$t("webhooks.trigger_realtime"),
        scheduled: this.$t("webhooks.trigger_scheduled"),
      };
      return typeMap[type] || type;
    },

    truncateText(text, maxLength) {
      if (!text || text.length <= maxLength) return text;
      return text.substring(0, maxLength) + "...";
    },

    getRowIndex(index) {
      return (this.currentPage - 1) * this.pageSize + index + 1;
    },

    getDeleteConfirmationMessage() {
      return this.$t("webhooks.delete_webhook_confirm", {
        name: this.selectedWebhook.name || "",
      });
    },

    async simulateApiCall(delay) {
      return new Promise((resolve) => setTimeout(resolve, delay));
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.page-title {
  margin-bottom: 1rem;
}

.action-bar {
  margin-bottom: 1rem;
  
  .create-button {
    margin-bottom: 0.5rem;
  }
}

.webhooks-table {
  .webhook-row {
    &:hover {
      background-color: #f4f4f4;
    }
  }

  .index-cell {
    text-align: center;
    font-weight: 600;
    color: #525252;
  }

  .toggle-cell {
    text-align: center;
  }

  .name-cell {
    .webhook-name {
      font-weight: 600;
      color: #161616;
    }
  }

  .url-cell {
    .webhook-url {
      font-family: "IBM Plex Mono", "Menlo", "DejaVu Sans Mono", "Bitstream Vera Sans Mono", Courier, monospace;
      color: #525252;
      font-size: 0.875rem;
    }
  }

  .email-cell {
    color: $text-02;
  }

  .payload-cell,
  .trigger-cell {
    text-align: center;
  }

  .action-cell {
    text-transform: capitalize;
  }

  .date-cell {
    .date-text {
      font-size: 0.875rem;
      color: #525252;
    }
  }

  .actions-cell {
    text-align: center;
    
    .webhook-actions-menu {
      width: auto;
    }
  }
}

.empty-state-button {
  margin-top: 1rem;
}

// Responsive adjustments
@media (max-width: 1024px) {
  .webhooks-table {
    .url-cell,
    .date-cell {
      font-size: 0.75rem;
    }
  }
}
</style>
