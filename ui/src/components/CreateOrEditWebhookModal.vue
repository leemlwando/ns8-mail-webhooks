<!--
  Copyright (C) 2025 Lee M. Lwando
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <NsModal
    size="default"
    :visible="isShown"
    @modal-hidden="$emit('hide')"
    @primary-click="saveWebhook"
    @secondary-click="$emit('hide')"
    :primary-button-disabled="loading.saveWebhook"
  >
    <template slot="title">{{
      isEditing ? $t("webhooks.edit_webhook") : $t("webhooks.create_webhook")
    }}</template>
    <template slot="content">
      <cv-form @submit.prevent="saveWebhook">
        <cv-dropdown
          v-model="webhookData.email"
          :label="$t('webhooks.email')"
          :disabled="loading.saveWebhook || loading.getEmailAddresses"
          :invalid-message="error.email"
          :light="true"
          ref="email"
          class="mg-bottom-md"
        >
          <cv-dropdown-item
            v-if="loading.getEmailAddresses"
            value=""
            disabled
          >
            {{ $t("common.processing") }}
          </cv-dropdown-item>
          <cv-dropdown-item
            v-else-if="!emailAddresses.length"
            value=""
            disabled
          >
            {{ $t("webhooks.no_email_addresses") }}
          </cv-dropdown-item>
          <cv-dropdown-item
            v-else
            v-for="email in emailAddresses"
            :key="email"
            :value="email"
          >
            {{ email }}
          </cv-dropdown-item>
        </cv-dropdown>

        <cv-text-input
          :label="$t('webhooks.url')"
          v-model="webhookData.url"
          :placeholder="$t('webhooks.url_placeholder')"
          :disabled="loading.saveWebhook"
          :invalid-message="error.url"
          ref="url"
          class="mg-bottom-md"
        ></cv-text-input>

        <cv-toggle
          :value="webhookData.enabled"
          @change="webhookData.enabled = $event"
          :disabled="loading.saveWebhook"
          class="mg-bottom-md"
        >
          <template slot="text-left">{{ $t("webhooks.disabled") }}</template>
          <template slot="text-right">{{ $t("webhooks.enabled") }}</template>
        </cv-toggle>

        <cv-checkbox
          :checked="webhookData.is_realtime"
          @change="webhookData.is_realtime = $event"
          :disabled="loading.saveWebhook"
          :label="$t('webhooks.realtime_monitoring')"
          class="mg-bottom-md"
        ></cv-checkbox>

          <cv-grid v-if="!webhookData.is_realtime" class="no-padding mg-bottom-md">
            <cv-row>
              <cv-column :md="4">
                <cv-dropdown
                  :label="$t('webhooks.schedule')"
                  v-model="webhookData.schedule_type"
                  :disabled="loading.saveWebhook"
                  :invalid-message="error.schedule_type"
                  :light="true"
                >
                  <cv-dropdown-item
                    v-for="option in scheduleTypeOptions"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.name }}
                  </cv-dropdown-item>
                </cv-dropdown>
              </cv-column>
              <cv-column :md="4" v-if="webhookData.schedule_type === 'hours'">
                <cv-dropdown
                  :label="$t('webhooks.interval')"
                  v-model.number="webhookData.schedule_hours"
                  :disabled="loading.saveWebhook"
                  :invalid-message="error.schedule_hours"
                  :light="true"
                >
                  <cv-dropdown-item
                    v-for="hour in hourOptions"
                    :key="hour"
                    :value="hour"
                  >
                    {{ $t('webhooks.every_hours', { count: hour }) }}
                  </cv-dropdown-item>
                </cv-dropdown>
              </cv-column>
              <cv-column :md="4" v-if="webhookData.schedule_type === 'custom'">
                <cv-text-input
                  :label="$t('webhooks.custom_interval')"
                  v-model="webhookData.schedule_custom"
                  :placeholder="$t('webhooks.custom_interval_placeholder')"
                  :disabled="loading.saveWebhook"
                  :invalid-message="error.schedule_custom"
                  :helper-text="$t('webhooks.custom_interval_help')"
                  @input="computeCustomInterval"
                  ref="schedule_custom"
                ></cv-text-input>
                <div v-if="computedInterval" class="custom-interval-result">
                  <small class="text-muted">
                    {{ $t('webhooks.computed_interval', { seconds: computedInterval }) }}
                  </small>
                </div>
              </cv-column>
            </cv-row>
          </cv-grid>

        <cv-dropdown
          :label="$t('webhooks.post_action')"
          v-model="webhookData.post_action"
          :disabled="loading.saveWebhook"
          :invalid-message="error.post_action"
          :light="true"
          class="mg-bottom-md"
        >
          <cv-dropdown-item
            v-for="option in postActionOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.name }}
          </cv-dropdown-item>
        </cv-dropdown>

        <cv-dropdown
          :label="$t('webhooks.payload_type')"
          v-model="webhookData.payload_type"
          :disabled="loading.saveWebhook"
          :invalid-message="error.payload_type"
          :light="true"
          class="mg-bottom-md"
        >
          <cv-dropdown-item
            v-for="option in payloadTypeOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.name }}
          </cv-dropdown-item>
        </cv-dropdown>

        <NsInlineNotification
          v-if="error.saveWebhook"
          kind="error"
          :title="$t('error.validation_error')"
          :description="error.saveWebhook"
          :showCloseButton="false"
        />
      </cv-form>
    </template>
    <template slot="secondary-button">{{ $t("common.cancel") }}</template>
    <template slot="primary-button">{{
      isEditing ? $t("common.save") : $t("common.create")
    }}</template>
  </NsModal>
</template>

<script>
import to from "await-to-js";
import { mapState } from "vuex";
import {
  UtilService,
  TaskService,
  IconService,
} from "@nethserver/ns8-ui-lib";

export default {
  name: "CreateOrEditWebhookModal",
  mixins: [UtilService, TaskService, IconService],
  props: {
    isShown: {
      type: Boolean,
      default: false,
    },
    webhook: Object,
    isEditing: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      webhookData: {
        email: "",
        url: "",
        enabled: true,
        is_realtime: true,
        schedule_type: "hours",
        schedule_hours: 1,
        schedule_custom: "",
        post_action: "none",
        payload_type: "json",
      },
      emailAddresses: [],
      computedInterval: null,
      loading: {
        saveWebhook: false,
        getEmailAddresses: false,
      },
      error: {
        saveWebhook: "",
        email: "",
        url: "",
        post_action: "",
        payload_type: "",
        schedule_type: "",
        schedule_hours: "",
        schedule_custom: "",
        getEmailAddresses: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core"]),
    postActionOptions() {
      return [
        {
          name: this.$t("webhooks.post_action_none"),
          value: "none",
        },
        {
          name: this.$t("webhooks.post_action_mark_as_read"),
          value: "mark_as_read",
        },
        {
          name: this.$t("webhooks.post_action_delete"),
          value: "delete",
        },
      ];
    },
    payloadTypeOptions() {
      return [
        {
          name: this.$t("webhooks.payload_type_json"),
          value: "json",
        },
        {
          name: this.$t("webhooks.payload_type_raw"),
          value: "raw",
        },
      ];
    },
    scheduleTypeOptions() {
      return [
        {
          name: this.$t("webhooks.schedule_type_hours"),
          value: "hours",
        },
        {
          name: this.$t("webhooks.schedule_type_custom"),
          value: "custom",
        },
      ];
    },
    hourOptions() {
      return Array.from({ length: 24 }, (_, i) => i + 1);
    },
  },
  watch: {
    webhook: {
      handler() {
        this.loadWebhookData();
      },
      immediate: true,
    },
    isShown: {
      handler(isShown) {
        if (isShown) {
          this.clearErrors();
          this.loadWebhookData();
          this.getEmailAddresses();
          // Focus first input field
          this.$nextTick(() => {
            this.focusElement("email");
          });
        }
      },
    },
  },
  methods: {
    loadWebhookData() {
      if (this.webhook) {
        // Editing existing webhook
        this.webhookData = {
          id: this.webhook.id,
          email: this.webhook.email,
          url: this.webhook.url,
          enabled: this.webhook.enabled,
          is_realtime: this.webhook.is_realtime !== undefined ? this.webhook.is_realtime : true,
          schedule_type: this.webhook.schedule_type || "hours",
          schedule_hours: parseInt(this.webhook.schedule_hours) || 1,
          schedule_custom: this.webhook.schedule_custom || "",
          post_action: this.webhook.post_action,
          payload_type: this.webhook.payload_type,
        };
      } else {
        // Creating new webhook
        this.webhookData = {
          email: "",
          url: "",
          enabled: true,
          is_realtime: true,
          schedule_type: "hours",
          schedule_hours: 1,
          schedule_custom: "",
          post_action: "none",
          payload_type: "json",
        };
      }
      
      // Reset computed interval when loading data
      this.computedInterval = null;
    },
    validateWebhookData() {
      this.clearErrors();
      let isValidationOk = true;

      // Validate email
      if (!this.webhookData.email) {
        this.error.email = this.$t("common.required");
        isValidationOk = false;
      } else if (!this.isValidEmail(this.webhookData.email)) {
        this.error.email = this.$t("error.invalid_email");
        isValidationOk = false;
      }

      // Validate URL
      if (!this.webhookData.url) {
        this.error.url = this.$t("common.required");
        isValidationOk = false;
      } else if (!this.isValidUrl(this.webhookData.url)) {
        this.error.url = this.$t("error.invalid_url");
        isValidationOk = false;
      }

      // Validate schedule settings for non-realtime webhooks
      if (!this.webhookData.is_realtime) {
        if (!this.webhookData.schedule_type) {
          this.error.schedule_type = this.$t("common.required");
          isValidationOk = false;
        }

        if (this.webhookData.schedule_type === "hours") {
          if (!this.webhookData.schedule_hours || this.webhookData.schedule_hours < 1 || this.webhookData.schedule_hours > 24) {
            this.error.schedule_hours = this.$t("webhooks.error.invalid_hours");
            isValidationOk = false;
          }
        } else if (this.webhookData.schedule_type === "custom") {
          if (!this.webhookData.schedule_custom) {
            this.error.schedule_custom = this.$t("common.required");
            isValidationOk = false;
          } else if (!this.isValidCustomInterval(this.webhookData.schedule_custom)) {
            this.error.schedule_custom = this.$t("webhooks.error.invalid_custom_interval");
            isValidationOk = false;
          }
        }
      }

      // Validate post_action
      if (!this.webhookData.post_action) {
        this.error.post_action = this.$t("common.required");
        isValidationOk = false;
      }

      // Validate payload_type
      if (!this.webhookData.payload_type) {
        this.error.payload_type = this.$t("common.required");
        isValidationOk = false;
      }

      return isValidationOk;
    },
    isValidEmail(email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    },
    isValidUrl(url) {
      try {
        const urlObj = new URL(url);
        return urlObj.protocol === "http:" || urlObj.protocol === "https:";
      } catch {
        return false;
      }
    },
    isValidCustomInterval(interval) {
      try {
        // Try to evaluate as math expression first
        const computed = this.evaluateMathExpression(interval);
        if (computed !== null) {
          return computed >= 60; // Minimum 1 minute
        }
        
        // Accept number format (seconds)
        if (/^\d+$/.test(interval)) {
          const seconds = parseInt(interval);
          return seconds >= 60; // Minimum 1 minute
        }
        
        // Accept HH:MM:SS or MM:SS format
        const timeRegex = /^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$/;
        const match = interval.match(timeRegex);
        if (match) {
          const hours = parseInt(match[1]) || 0;
          const minutes = parseInt(match[2]);
          const seconds = parseInt(match[3]) || 0;
          
          // Validate ranges
          if (minutes >= 60 || seconds >= 60) return false;
          
          // Calculate total seconds
          const totalSeconds = hours * 3600 + minutes * 60 + seconds;
          return totalSeconds >= 60; // Minimum 1 minute
        }
        
        return false;
      } catch (e) {
        return false;
      }
    },
    evaluateMathExpression(expression) {
      try {
        // Only allow numbers, +, -, *, /, (, ), and whitespace
        if (!/^[\d+\-*/\s().]+$/.test(expression)) {
          return null;
        }
        
        // Use Function constructor to safely evaluate math expressions
        const result = new Function('return ' + expression)();
        
        if (typeof result === 'number' && !isNaN(result) && isFinite(result)) {
          return Math.floor(result);
        }
        
        return null;
      } catch (e) {
        return null;
      }
    },
    computeCustomInterval() {
      if (this.webhookData.schedule_custom) {
        const computed = this.evaluateMathExpression(this.webhookData.schedule_custom);
        this.computedInterval = computed;
      } else {
        this.computedInterval = null;
      }
    },
    clearErrors() {
      this.error.saveWebhook = "";
      this.error.email = "";
      this.error.url = "";
      this.error.post_action = "";
      this.error.payload_type = "";
      this.error.schedule_type = "";
      this.error.schedule_hours = "";
      this.error.schedule_custom = "";
      this.error.getEmailAddresses = "";
    },
    async getEmailAddresses() {
      this.loading.getEmailAddresses = true;
      this.error.getEmailAddresses = "";
      const taskAction = "list-email-addresses";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.getEmailAddressesAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.getEmailAddressesCompleted
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
        this.error.getEmailAddresses = this.getErrorMessage(err);
        this.loading.getEmailAddresses = false;
        return;
      }
    },
    getEmailAddressesAborted() {
      // Task aborted - handle error
      this.error.getEmailAddresses = this.$t("error.generic_error");
      this.loading.getEmailAddresses = false;
    },
    getEmailAddressesCompleted(taskContext, taskResult) {
      this.loading.getEmailAddresses = false;
      this.emailAddresses = taskResult.output;
    },
    async saveWebhook() {
      if (!this.validateWebhookData()) {
        return;
      }

      this.loading.saveWebhook = true;
      this.error.saveWebhook = "";

      const taskAction = this.isEditing ? "edit-webhook" : "add-webhook";
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

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: this.webhookData,
          extra: {
            title: this.$t("action." + taskAction),
            description: this.isEditing
              ? this.$t("webhooks.editing_webhook", {
                  email: this.webhookData.email,
                })
              : this.$t("webhooks.creating_webhook", {
                  email: this.webhookData.email,
                }),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        // Error creating task - log for debugging
        this.error.saveWebhook = this.getErrorMessage(err);
        this.loading.saveWebhook = false;
        return;
      }
    },
    saveWebhookAborted() {
      // Task aborted - handle error
      this.error.saveWebhook = this.$t("error.generic_error");
      this.loading.saveWebhook = false;
    },
    saveWebhookCompleted(taskContext, taskResult) {
      this.loading.saveWebhook = false;

      // Emit success event to parent
      if (this.isEditing) {
        this.$emit("webhookEdited", taskResult.output);
      } else {
        this.$emit("webhookCreated", taskResult.output);
      }
    },
  },
};
</script>

<style scoped>
.mg-bottom-md {
  margin-bottom: 1rem;
}
</style>
