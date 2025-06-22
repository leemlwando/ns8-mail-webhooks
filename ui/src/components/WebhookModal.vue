<!--
  Copyright (C) 2025 Leemlwando
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-modal
    :visible="visible"
    :auto-hide-off="true"
    :primary-button-disabled="loading"
    @primary-click="handleSave"
    @secondary-click="handleClose"
    @modal-hidden="handleClose"
    @modal-hide-request="handleClose"
    size="large"
    class="webhook-modal"
  >
    <template slot="title">
      <div class="modal-title-container">
        <span>{{
          webhook.id
            ? $t("webhooks.edit_webhook")
            : $t("webhooks.create_webhook")
        }}</span>
      </div>
    </template>

    <template slot="content">
      <cv-form @submit.prevent="handleSave">
        <cv-text-input
          :label="$t('webhooks.name')"
          v-model="localWebhook.name"
          :placeholder="$t('webhooks.name_placeholder')"
          :disabled="loading"
          :invalid-message="errors.name"
          ref="name"
          class="mg-bottom-sm"
        ></cv-text-input>

        <cv-text-input
          :label="$t('webhooks.url')"
          v-model="localWebhook.url"
          :placeholder="$t('webhooks.url_placeholder')"
          :disabled="loading"
          :invalid-message="errors.url"
          ref="url"
          class="mg-bottom-sm"
        ></cv-text-input>

        <cv-text-input
          :label="$t('webhooks.api_key')"
          v-model="localWebhook.api_key"
          :placeholder="$t('webhooks.api_key_placeholder')"
          :disabled="loading"
          :invalid-message="errors.api_key"
          ref="apiKey"
          class="mg-bottom-sm"
        ></cv-text-input>

        <cv-dropdown
          :label="$t('webhooks.email_address')"
          v-model="localWebhook.email_address"
          :options="emailOptions"
          :disabled="loading"
          :invalid-message="errors.email_address"
          ref="emailAddress"
          class="mg-bottom-sm"
        ></cv-dropdown>

        <cv-dropdown
          :label="$t('webhooks.payload_type')"
          v-model="localWebhook.payload_type"
          :options="payloadTypeOptions"
          :disabled="loading"
          :invalid-message="errors.payload_type"
          ref="payloadType"
          class="mg-bottom-sm"
        ></cv-dropdown>

        <cv-dropdown
          :label="$t('webhooks.post_action')"
          v-model="localWebhook.post_action"
          :options="postActionOptions"
          :disabled="loading"
          :invalid-message="errors.post_action"
          ref="postAction"
          class="mg-bottom-sm"
        ></cv-dropdown>

        <cv-dropdown
          :label="$t('webhooks.trigger_type')"
          v-model="localWebhook.trigger_type"
          :options="triggerTypeOptions"
          :disabled="loading"
          :invalid-message="errors.trigger_type"
          ref="triggerType"
          class="mg-bottom-sm"
          @change="onTriggerTypeChange"
        ></cv-dropdown>

        <!-- Schedule interval selection (shown only for scheduled triggers) -->
        <cv-dropdown
          v-if="localWebhook.trigger_type === 'scheduled'"
          :label="$t('webhooks.schedule_interval')"
          v-model="localWebhook.schedule_interval"
          :options="scheduleIntervalOptions"
          :disabled="loading"
          :invalid-message="errors.schedule_interval"
          ref="scheduleInterval"
          class="mg-bottom-sm"
        ></cv-dropdown>

        <cv-toggle
          :label="$t('webhooks.enabled')"
          v-model="localWebhook.enabled"
          :disabled="loading"
          class="mg-bottom-sm"
        >
          <template slot="text-left">{{ $t("common.disabled") }}</template>
          <template slot="text-right">{{ $t("common.enabled") }}</template>
        </cv-toggle>
      </cv-form>

      <!-- Error notification -->
      <cv-row v-if="error">
        <cv-column>
          <NsInlineNotification
            kind="error"
            :title="$t('error.cannot_save_webhook')"
            :description="error"
            :showCloseButton="false"
          />
        </cv-column>
      </cv-row>
    </template>

    <template slot="secondary-button">{{ $t("common.cancel") }}</template>
    <template slot="primary-button">
      {{ loading ? $t("common.saving") : $t("common.save") }}
    </template>
  </cv-modal>
</template>

<script>
import { UtilService } from "@nethserver/ns8-ui-lib";

export default {
  name: "WebhookModal",
  mixins: [UtilService],
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    webhook: {
      type: Object,
      default: () => ({}),
    },
    loading: {
      type: Boolean,
      default: false,
    },
    error: {
      type: String,
      default: "",
    },
  },
  data() {
    return {
      localWebhook: {},
      errors: {},
      emailOptions: [
        { label: "admin@example.com", value: "admin@example.com" },
        { label: "orders@example.com", value: "orders@example.com" },
        { label: "support@example.com", value: "support@example.com" },
        { label: "marketing@example.com", value: "marketing@example.com" },
        { label: "sales@example.com", value: "sales@example.com" },
      ],
    };
  },
  computed: {
    payloadTypeOptions() {
      return [
        { label: this.$t("webhooks.payload_json"), value: "json" },
        { label: this.$t("webhooks.payload_raw"), value: "raw" },
      ];
    },
    postActionOptions() {
      return [
        { label: this.$t("webhooks.action_none"), value: "none" },
        { label: this.$t("webhooks.action_mark_read"), value: "mark as read" },
        { label: this.$t("webhooks.action_delete"), value: "delete" },
      ];
    },
    triggerTypeOptions() {
      return [
        { label: this.$t("webhooks.trigger_realtime"), value: "real time" },
        { label: this.$t("webhooks.trigger_scheduled"), value: "scheduled" },
      ];
    },
    scheduleIntervalOptions() {
      return [
        { label: this.$t("webhooks.interval_5min"), value: "5min" },
        { label: this.$t("webhooks.interval_15min"), value: "15min" },
        { label: this.$t("webhooks.interval_30min"), value: "30min" },
        { label: this.$t("webhooks.interval_1hour"), value: "1hour" },
        { label: this.$t("webhooks.interval_6hours"), value: "6hours" },
        { label: this.$t("webhooks.interval_12hours"), value: "12hours" },
        { label: this.$t("webhooks.interval_24hours"), value: "24hours" },
      ];
    },
  },
  watch: {
    webhook: {
      handler(newVal) {
        this.localWebhook = { ...newVal };
        this.clearErrors();
      },
      deep: true,
      immediate: true,
    },
    visible(newVal) {
      if (newVal && this.localWebhook.name) {
        this.$nextTick(() => {
          this.focusElement("name");
        });
      }
      // Clear errors when modal is hidden
      if (!newVal) {
        this.clearErrors();
      }
    },
  },
  methods: {
    handleSave() {
      if (this.validateForm()) {
        this.$emit("save", { ...this.localWebhook });
      }
    },

    handleClose() {
      this.$emit("close");
      this.clearErrors();
    },

    validateForm() {
      this.clearErrors();
      let isValid = true;

      if (!this.localWebhook.name) {
        this.errors.name = this.$t("common.required");
        isValid = false;
      }

      if (!this.localWebhook.url) {
        this.errors.url = this.$t("common.required");
        isValid = false;
      } else if (!this.isValidUrl(this.localWebhook.url)) {
        this.errors.url = this.$t("webhooks.invalid_url");
        isValid = false;
      }

      if (!this.localWebhook.email_address) {
        this.errors.email_address = this.$t("common.required");
        isValid = false;
      }

      if (!this.localWebhook.payload_type) {
        this.errors.payload_type = this.$t("common.required");
        isValid = false;
      }

      if (!this.localWebhook.post_action) {
        this.errors.post_action = this.$t("common.required");
        isValid = false;
      }

      if (!this.localWebhook.trigger_type) {
        this.errors.trigger_type = this.$t("common.required");
        isValid = false;
      }

      if (
        this.localWebhook.trigger_type === "scheduled" &&
        !this.localWebhook.schedule_interval
      ) {
        this.errors.schedule_interval = this.$t("common.required");
        isValid = false;
      }

      return isValid;
    },

    clearErrors() {
      this.errors = {};
    },

    isValidUrl(url) {
      try {
        new URL(url);
        return true;
      } catch {
        return false;
      }
    },

    onTriggerTypeChange(value) {
      if (value !== "scheduled") {
        this.localWebhook.schedule_interval = "";
      }
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.modal-title-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.modal-close-btn {
  padding: 0.25rem;
  min-height: auto;

  :deep(.bx--btn__icon) {
    margin: 0;
  }
}

.webhook-modal {
  :deep(.bx--modal-container) {
    max-width: 600px;
    width: 90vw;
  }

  :deep(.bx--modal) {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9000;
  }

  :deep(.bx--modal-header__heading) {
    width: 100%;
  }

  :deep(.bx--modal-content) {
    max-height: calc(100vh - 200px);
    overflow-y: auto;
  }

  :deep(.bx--form-item) {
    margin-bottom: 0.5rem;
  }
}
</style>
