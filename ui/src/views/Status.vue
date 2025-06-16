<!--
  Copyright (C) 2023 Lee M. Lwando <leemlwando@gmail.com>
  SPDX-License-Identifier: MIT
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("status.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getStatus">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-status')"
          :description="error.getStatus"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column :md="4" :max="4">
        <NsInfoCard
          light
          :title="status.instance || '-'"
          :description="$t('status.app_instance')"
          :icon="Application32"
          :loading="loading.getStatus"
          class="min-height-card"
        />
      </cv-column>
      <cv-column :md="4" :max="4">
        <NsInfoCard
          light
          :title="installationNodeTitle"
          :titleTooltip="installationNodeTitleTooltip"
          :description="$t('status.installation_node')"
          :icon="Chip32"
          :loading="loading.getStatus"
          class="min-height-card"
        />
      </cv-column>
      <cv-column :md="4" :max="4">
        <NsInfoCard
          light
          :title="status.version || '-'"
          :description="$t('status.module_version')"
          :icon="Version32"
          :loading="loading.getStatus"
          class="min-height-card"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column :md="6" :max="6">
        <NsInfoCard
          light
          :title="schedulerStatusTitle"
          :description="$t('status.scheduler_status')"
          :icon="schedulerStatusIcon"
          :iconClass="schedulerStatusIconClass"
          :loading="loading.getStatus"
          class="min-height-card"
        />
      </cv-column>
      <cv-column :md="6" :max="6">
        <NsSystemLogsCard
          :title="core.$t('system_logs.card_title')"
          :description="
            core.$t('system_logs.card_description', {
              name: instanceLabel || instanceName,
            })
          "
          :buttonLabel="core.$t('system_logs.card_button_label')"
          :router="core.$router"
          context="module"
          :moduleId="instanceName"
          light
        />
      </cv-column>
    </cv-row>
    <!-- services -->
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $tc("status.services", 2) }}</h4>
      </cv-column>
    </cv-row>
    <cv-row v-if="!loading.getStatus">
      <cv-column v-if="!status.services.length">
        <cv-tile light>
          <NsEmptyState :title="$t('status.no_services')"> </NsEmptyState>
        </cv-tile>
      </cv-column>
      <cv-column
        v-else
        v-for="(service, index) in status.services"
        :key="index"
        :md="4"          :contextId="instanceName"
          :core="core"
          light
        />
      </cv-column>
    </cv-row>
    <!-- Processing Statistics -->
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $t("status.processing_statistics") }}</h4>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column :md="4" :max="4">
        <NsInfoCard
          light
          :title="(processingStats.total_processed || 0).toString()"
          :description="$t('status.total_emails_processed')"
          :icon="Email32"
          :loading="loading.getStatus"
          class="min-height-card"
        />
      </cv-column>
      <cv-column :md="4" :max="4">
        <NsInfoCard
          light
          :title="(processingStats.successful || 0).toString()"
          :description="$t('status.successful_webhooks')"
          :icon="CheckmarkOutline32"
          :loading="loading.getStatus"
          class="min-height-card status-success"
        />
      </cv-column>
      <cv-column :md="4" :max="4">
        <NsInfoCard
          light
          :title="(processingStats.failed || 0).toString()"
          :description="$t('status.failed_webhooks')"
          :icon="WarningAlt32"
          :loading="loading.getStatus"
          class="min-height-card status-warning"
        />
      </cv-column>
    </cv-row>
    <!-- Active Schedules -->
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $t("status.active_schedules") }}</h4>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <div v-if="!loading.getStatus">
            <NsEmptyState
              v-if="!activeSchedules.length"
              :title="$t('status.no_active_schedules')"
              :description="$t('status.no_active_schedules_description')"
            >
            </NsEmptyState>
            <cv-structured-list v-else>
              <template slot="headings">
                <cv-structured-list-heading>{{
                  $t("status.email_address")
                }}</cv-structured-list-heading>
                <cv-structured-list-heading>{{
                  $t("status.webhook_url")
                }}</cv-structured-list-heading>
                <cv-structured-list-heading>{{
                  $t("status.last_run")
                }}</cv-structured-list-heading>
                <cv-structured-list-heading>{{
                  $t("status.status")
                }}</cv-structured-list-heading>
              </template>
              <template slot="items">
                <cv-structured-list-item
                  v-for="(schedule, index) in activeSchedules"
                  :key="index"
                >
                  <cv-structured-list-data class="break-word">{{
                    schedule.email_address
                  }}</cv-structured-list-data>
                  <cv-structured-list-data class="break-word">{{
                    schedule.webhook_url
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>{{
                    schedule.last_run ? formatDate(schedule.last_run) : '-'
                  }}</cv-structured-list-data>
                  <cv-structured-list-data>
                    <cv-tag 
                      :label="schedule.enabled ? $t('common.enabled') : $t('common.disabled')"
                      :kind="schedule.enabled ? 'green' : 'gray'"
                    />
                  </cv-structured-list-data>
                </cv-structured-list-item>
              </template>
            </cv-structured-list>
          </div>
          <cv-skeleton-text
            v-else
            :paragraph="true"
            :line-count="5"
          ></cv-skeleton-text>
        </cv-tile>
      </cv-column>
    </cv-row>
  </cv-grid>
</template>

<script>
import to from "await-to-js";
import { mapState } from "vuex";
import {
  QueryParamService,
  TaskService,
  IconService,
  UtilService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";
import {
  Application32,
  Chip32,
  Version32,
  Email32,
  CheckmarkOutline32,
  WarningAlt32,
} from "@carbon/icons-vue";
import UtilMixin from "@/mixins/util.js";

export default {
  name: "Status",
  components: {
    Application32,
    Chip32,
    Version32,
    Email32,
    CheckmarkOutline32,
    WarningAlt32,  },
  mixins: [
    TaskService,
    QueryParamService,
    IconService,
    UtilService,
    PageTitleService,
    UtilMixin,
  ],
  pageTitle() {
    return this.$t("status.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "status",
      },
      urlCheckInterval: null,
      isRedirectChecked: false,
      redirectTimeout: 0,
      status: {
        instance: "",
        version: "",
        scheduler_running: false,
      },
      processingStats: {
        total_processed: 0,
        successful: 0,
        failed: 0,
      },
      activeSchedules: [],
      loading: {
        getStatus: false,
      },
      error: {
        getStatus: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "instanceLabel", "core", "appName"]),
    installationNodeTitle() {
      if (this.status && this.status.node) {
        if (this.status.node_ui_name) {
          return this.status.node_ui_name;
        } else {
          return this.$t("status.node") + " " + this.status.node;
        }
      } else {
        return "-";
      }
    },
    installationNodeTitleTooltip() {
      if (this.status && this.status.node_ui_name) {
        return this.$t("status.node") + " " + this.status.node;
      } else {
        return "";
      }
    },
    schedulerStatusTitle() {
      return this.status.scheduler_running 
        ? this.$t('status.scheduler_running')
        : this.$t('status.scheduler_stopped');
    },    schedulerStatusIcon() {
      return this.status.scheduler_running ? CheckmarkOutline32 : WarningAlt32;
    },
    schedulerStatusIconClass() {
      return this.status.scheduler_running ? 'status-success' : 'status-warning';
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
  mounted() {
    this.redirectTimeout = setTimeout(
      () => (this.isRedirectChecked = true),
      200
    );
  },
  beforeUnmount() {
    clearTimeout(this.redirectTimeout);
  },
  created() {
    this.getStatus();
    this.getSchedules();
    this.getProcessingStats();
  },
  methods: {
    async getStatus() {
      this.loading.getStatus = true;
      this.error.getStatus = "";

      try {
        const response = await this.axios.get(`${this.apiUrl}/api/status`);
        this.status = response.data;
      } catch (error) {
        console.error('Error fetching status:', error);
        this.error.getStatus = this.getErrorMessage(error);
      } finally {
        this.loading.getStatus = false;
      }
    },
    async getSchedules() {
      try {
        const response = await this.axios.get(`${this.apiUrl}/api/schedules/`);
        this.activeSchedules = response.data || [];
      } catch (error) {
        console.error('Error fetching schedules:', error);
      }
    },
    async getProcessingStats() {
      try {
        const response = await this.axios.get(`${this.apiUrl}/api/logs/`);
        const logs = response.data || [];
        
        this.processingStats = {
          total_processed: logs.length,
          successful: logs.filter(log => log.status === 'success').length,
          failed: logs.filter(log => log.status === 'error').length,
        };
      } catch (error) {
        console.error('Error fetching processing stats:', error);
      }
    },
    formatDate(dateString) {
      if (!dateString) return '-';
      return new Date(dateString).toLocaleString();
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.break-word {
  word-wrap: break-word;
  max-width: 30vw;
}

.status-success .bx--info-card__icon {
  color: #198038;
}

.status-warning .bx--info-card__icon {
  color: #f1c21b;
}
