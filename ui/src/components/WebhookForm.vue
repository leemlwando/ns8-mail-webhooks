<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-form @submit.prevent>
    <cv-text-input
      :label="$t('webhooks.webhook_name')"
      v-model="webhookForm.name"
      :placeholder="$t('webhooks.webhook_name')"
      :disabled="loading"
      :invalid-message="validationErrors.name"
      ref="name"
      class="mg-bottom-md"
    ></cv-text-input>

    <cv-text-input
      :label="$t('webhooks.webhook_url')"
      v-model="webhookForm.url"
      :placeholder="'https://example.com/webhook'"
      :disabled="loading"
      :invalid-message="validationErrors.url"
      ref="url"
      class="mg-bottom-md"
    ></cv-text-input>

    <cv-text-input
      :label="$t('webhooks.api_key')"
      v-model="webhookForm.api_key"
      :placeholder="$t('webhooks.api_key_placeholder')"
      :disabled="loading"
      :invalid-message="validationErrors.api_key"
      ref="api_key"
      type="password"
      class="mg-bottom-md"
    ></cv-text-input>

    <cv-row class="mg-bottom-md">
      <cv-column :md="4">
        <cv-dropdown
          :label="$t('webhooks.payload_type')"
          v-model="webhookForm.payload_type"
          :disabled="loading"
        >
          <cv-dropdown-item value="JSON">
            {{ $t("webhooks.json_format") }}
          </cv-dropdown-item>
          <cv-dropdown-item value="RAW">
            {{ $t("webhooks.raw_format") }}
          </cv-dropdown-item>
        </cv-dropdown>
      </cv-column>
      <cv-column :md="4">
        <cv-dropdown
          :label="$t('webhooks.trigger_type')"
          v-model="webhookForm.trigger_type"
          :disabled="loading"
        >
          <cv-dropdown-item value="realtime">
            {{ $t("webhooks.realtime") }}
          </cv-dropdown-item>
          <cv-dropdown-item value="interval">
            {{ $t("webhooks.interval_based") }}
          </cv-dropdown-item>
        </cv-dropdown>
      </cv-column>
    </cv-row>

    <cv-text-input
      v-if="webhookForm.trigger_type === 'interval'"
      :label="$t('webhooks.interval')"
      v-model.number="webhookForm.interval"
      :placeholder="'300'"
      :disabled="loading"
      :invalid-message="validationErrors.interval"
      ref="interval"
      type="number"
      class="mg-bottom-md"
    ></cv-text-input>

    <cv-text-area
      :label="$t('webhooks.mailboxes')"
      v-model="mailboxesText"
      :placeholder="$t('webhooks.mailboxes_placeholder')"
      :disabled="loading"
      :invalid-message="validationErrors.mailboxes"
      ref="mailboxes"
      rows="3"
      class="mg-bottom-md"
    ></cv-text-area>

    <cv-text-area
      :label="$t('webhooks.filters')"
      v-model="filtersText"
      :placeholder="$t('webhooks.filters_placeholder')"
      :disabled="loading"
      :invalid-message="validationErrors.filters"
      ref="filters"
      rows="4"
      class="mg-bottom-md"
    ></cv-text-area>

    <cv-checkbox
      :label="$t('webhooks.active')"
      v-model="webhookForm.active"
      :disabled="loading"
      class="mg-bottom-md"
    ></cv-checkbox>
  </cv-form>
</template>

<script>
export default {
  name: "WebhookForm",
  props: {
    webhook: {
      type: Object,
      default: () => ({
        name: "",
        url: "",
        api_key: "",
        payload_type: "JSON",
        trigger_type: "realtime",
        interval: 300,
        mailboxes: [],
        filters: {},
        active: true,
      }),
    },
    loading: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      webhookForm: { ...this.webhook },
      validationErrors: {
        name: "",
        url: "",
        api_key: "",
        interval: "",
        mailboxes: "",
        filters: "",
      },
    };
  },
  computed: {
    mailboxesText: {
      get() {
        return Array.isArray(this.webhookForm.mailboxes)
          ? this.webhookForm.mailboxes.join("\n")
          : "";
      },
      set(value) {
        this.webhookForm.mailboxes = value
          ? value.split("\n").filter((line) => line.trim())
          : [];
        this.emitUpdate();
      },
    },
    filtersText: {
      get() {
        try {
          return JSON.stringify(this.webhookForm.filters, null, 2);
        } catch {
          return "";
        }
      },
      set(value) {
        try {
          this.webhookForm.filters = value ? JSON.parse(value) : {};
          this.validationErrors.filters = "";
        } catch (error) {
          this.validationErrors.filters = this.$t("webhooks.invalid_json");
        }
        this.emitUpdate();
      },
    },
  },
  watch: {
    webhook: {
      handler(newWebhook) {
        this.webhookForm = { ...newWebhook };
      },
      deep: true,
      immediate: true,
    },
    webhookForm: {
      handler() {
        this.emitUpdate();
      },
      deep: true,
    },
  },
  methods: {
    validate() {
      this.clearValidationErrors();
      let isValid = true;

      // Validate required fields
      if (!this.webhookForm.name.trim()) {
        this.validationErrors.name = this.$t("webhooks.webhook_name_required");
        isValid = false;
      }

      if (!this.webhookForm.url.trim()) {
        this.validationErrors.url = this.$t("webhooks.webhook_url_required");
        isValid = false;
      } else if (!this.isValidUrl(this.webhookForm.url)) {
        this.validationErrors.url = this.$t("webhooks.invalid_url");
        isValid = false;
      }

      // Validate interval for interval-based triggers
      if (this.webhookForm.trigger_type === "interval") {
        if (!this.webhookForm.interval || this.webhookForm.interval <= 0) {
          this.validationErrors.interval = this.$t("webhooks.invalid_interval");
          isValid = false;
        }
      }

      // Validate JSON filters
      if (this.filtersText.trim()) {
        try {
          JSON.parse(this.filtersText);
        } catch {
          this.validationErrors.filters = this.$t("webhooks.invalid_json");
          isValid = false;
        }
      }

      return isValid;
    },
    clearValidationErrors() {
      Object.keys(this.validationErrors).forEach((key) => {
        this.validationErrors[key] = "";
      });
    },
    isValidUrl(string) {
      try {
        new URL(string);
        return true;
      } catch {
        return false;
      }
    },
    emitUpdate() {
      this.$emit("input", { ...this.webhookForm });
    },
  },
};
</script>

<style scoped lang="scss">
.mg-bottom-md {
  margin-bottom: 1rem;
}
</style>
