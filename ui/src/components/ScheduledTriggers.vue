<!--
Copyright (C) 2023 Lee M. Lwando <leemlwando@gmail.com>
SPDX-License-Identifier: MIT
-->
<template>
  <cv-grid class="tab-content">
    <cv-row>
      <cv-column>
        <div class="tab-description">
          <p>{{ $t("webhooks.scheduled_triggers_description") }}</p>
        </div>
        <cv-button @click="showAddModal = true" kind="primary">
          {{ $t("webhooks.add_schedule") }}
        </cv-button>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-data-table
          :columns="columns"
          :data="schedules"
          :loading="loading"
          ref="table"
          v-model:sort-by="sortBy"
        >
          <template #cell-is_active="{ row, value }">
            <cv-toggle
              :checked="value"
              @change="toggleScheduleStatus(row.id, $event)"
              :value="value"
              size="small"
            >
              <span class="toggle-label">{{ 
                value ? $t("webhooks.active") : $t("webhooks.paused") 
              }}</span>
            </cv-toggle>
          </template>
          <template #cell-actions="{ row }">
            <cv-overflow-menu flip-menu>
              <cv-overflow-menu-item @click="editSchedule(row)">
                {{ $t("common.edit") }}
              </cv-overflow-menu-item>
              <cv-overflow-menu-item @click="confirmDelete(row)" danger>
                {{ $t("common.delete") }}
              </cv-overflow-menu-item>
            </cv-overflow-menu>
          </template>
        </cv-data-table>
      </cv-column>
    </cv-row>

    <!-- Add/Edit Schedule Modal -->
    <cv-modal
      :visible="showAddModal"
      @modal-hidden="showAddModal = false"
      :primary-button-disabled="!isModalValid"
      @primary-click="saveSchedule"
      size="default"
    >
      <template #title>
        {{ isEditing ? $t("webhooks.edit_trigger") : $t("webhooks.add_trigger") }}
      </template>
      <template #content>
        <cv-form>
          <cv-text-input
            :label="$t('webhooks.mailbox_to_monitor')"
            v-model.trim="currentSchedule.mailbox_to_monitor"
            :placeholder="$t('webhooks.mailbox_placeholder')"
            :invalid="errors.mailbox_to_monitor"
            :invalid-message="errors.mailbox_to_monitor"
          />
          <cv-text-input
            :label="$t('webhooks.webhook_url')"
            v-model.trim="currentSchedule.webhook_url"
            :placeholder="$t('webhooks.webhook_url_placeholder')"
            :invalid="errors.webhook_url"
            :invalid-message="errors.webhook_url"
          />
          <cv-text-input
            :label="$t('webhooks.api_key_optional')"
            v-model.trim="currentSchedule.api_key"
            password
            :placeholder="$t('webhooks.api_key_placeholder')"
          />
          <cv-form-group :legend-text="$t('webhooks.payload_format')">
            <cv-radio-group v-model="currentSchedule.payload_format">
              <cv-radio-button label="RAW" value="RAW" />
              <cv-radio-button label="JSON" value="JSON" />
            </cv-radio-group>
          </cv-form-group>
        </cv-form>
      </template>
    </cv-modal>
    
    <!-- Delete Confirmation Modal -->
    <cv-modal
      :visible="showDeleteConfirm"
      @modal-hidden="showDeleteConfirm = false"
      @primary-click="deleteSchedule"
      danger
      size="small"
    >
      <template #title>{{ $t("common.confirm_delete") }}</template>
      <template #content>
        <p>
          {{ $t("webhooks.delete_confirmation", { 
            mailbox: currentSchedule.mailbox_to_monitor 
          }) }}
        </p>
      </template>
    </cv-modal>
  </cv-grid>
</template>

<script>
import { UtilService } from "@/mixins/util";

const emptySchedule = {
  mailbox_to_monitor: "",
  webhook_url: "",
  api_key: "",
  payload_format: "RAW",
  is_active: true,
};

export default {
  name: "ScheduledTriggers",
  mixins: [UtilService],
  data() {
    return {
      loading: false,
      columns: [
        { 
          key: "mailbox_to_monitor", 
          label: this.$t("webhooks.mailbox_to_monitor"), 
          sortable: true 
        },
        { 
          key: "webhook_url", 
          label: this.$t("webhooks.webhook_url") 
        },
        { 
          key: "is_active", 
          label: this.$t("webhooks.status") 
        },
        { 
          key: "actions", 
          label: this.$t("common.actions"), 
          sortable: false 
        },
      ],
      schedules: [],
      showAddModal: false,
      showDeleteConfirm: false,
      isEditing: false,
      currentSchedule: { ...emptySchedule },
      sortBy: "",
      errors: {},
    };
  },
  computed: {
    isModalValid() {
      return (
        this.currentSchedule.mailbox_to_monitor &&
        this.currentSchedule.webhook_url &&
        this.isValidEmail(this.currentSchedule.mailbox_to_monitor) &&
        this.isValidUrl(this.currentSchedule.webhook_url)
      );
    },
  },
  methods: {
    async fetchSchedules() {
      this.loading = true;
      try {
        const response = await this.axios.get("/api/schedules/");
        this.schedules = response.data;
      } catch (error) {
        this.createErrorNotification(
          error,
          this.$t("error.cannot_retrieve_schedules")
        );
      } finally {
        this.loading = false;
      }
    },
    
    validateForm() {
      this.errors = {};
      
      if (!this.currentSchedule.mailbox_to_monitor) {
        this.errors.mailbox_to_monitor = this.$t("common.required_field");
      } else if (!this.isValidEmail(this.currentSchedule.mailbox_to_monitor)) {
        this.errors.mailbox_to_monitor = this.$t("error.invalid_email");
      }
      
      if (!this.currentSchedule.webhook_url) {
        this.errors.webhook_url = this.$t("common.required_field");
      } else if (!this.isValidUrl(this.currentSchedule.webhook_url)) {
        this.errors.webhook_url = this.$t("error.invalid_url");
      }
      
      return Object.keys(this.errors).length === 0;
    },
    
    async saveSchedule() {
      if (!this.validateForm()) {
        return;
      }
      
      try {
        if (this.isEditing) {
          await this.axios.put(
            `/api/schedules/${this.currentSchedule.id}`, 
            this.currentSchedule
          );
        } else {
          await this.axios.post("/api/schedules/", this.currentSchedule);
        }
        
        this.showAddModal = false;
        this.fetchSchedules();
        
        this.createSuccessNotification({
          title: this.$t("webhooks.schedule_saved"),
        });
      } catch (error) {
        this.createErrorNotification(
          error,
          this.$t("error.cannot_save_schedule")
        );
      }
    },
    
    editSchedule(schedule) {
      this.isEditing = true;
      this.currentSchedule = { ...schedule };
      this.showAddModal = true;
    },
    
    confirmDelete(schedule) {
      this.currentSchedule = { ...schedule };
      this.showDeleteConfirm = true;
    },
    
    async deleteSchedule() {
      try {
        await this.axios.delete(`/api/schedules/${this.currentSchedule.id}`);
        this.showDeleteConfirm = false;
        this.fetchSchedules();
        
        this.createSuccessNotification({
          title: this.$t("webhooks.schedule_deleted"),
        });
      } catch (error) {
        this.createErrorNotification(
          error,
          this.$t("error.cannot_delete_schedule")
        );
      }
    },
    
    async toggleScheduleStatus(id, newStatus) {
      try {
        const scheduleToUpdate = this.schedules.find(s => s.id === id);
        await this.axios.put(`/api/schedules/${id}`, { 
          ...scheduleToUpdate, 
          is_active: newStatus 
        });
        
        this.createSuccessNotification({
          title: this.$t(
            newStatus ? "webhooks.schedule_activated" : "webhooks.schedule_paused"
          ),
        });
        
        this.fetchSchedules(); // Refresh to ensure data consistency
      } catch (error) {
        this.createErrorNotification(
          error,
          this.$t("error.cannot_update_status")
        );
      }
    },
  },
  
  created() {
    this.fetchSchedules();
  },
  
  watch: {
    showAddModal(newVal) {
      if (!newVal) {
        this.isEditing = false;
        this.currentSchedule = { ...emptySchedule };
        this.errors = {};
      }
    }
  }
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

.toggle-label {
  margin-left: 0.5rem;
  font-size: 0.875rem;
}
</style>
