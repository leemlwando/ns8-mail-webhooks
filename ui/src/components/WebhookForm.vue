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

    <!-- Advanced Trigger Configuration -->
    <cv-accordion v-if="webhookForm.trigger_type" style="margin-top: 1rem;">
      <cv-accordion-item>
        <template slot="title">{{
          $t("webhooks.advanced_trigger_config")
        }}</template>
        <template slot="content">
          <cv-row v-if="webhookForm.trigger_type === 'interval'">
            <cv-column :md="6">
              <cv-text-input
                :label="$t('webhooks.interval_seconds')"
                v-model.number="webhookForm.trigger_config.interval_seconds"
                :placeholder="'300'"
                :disabled="loading"
                :invalid-message="validationErrors.interval_seconds"
                type="number"
                min="60"
              ></cv-text-input>
            </cv-column>
          </cv-row>
          
          <cv-row>
            <cv-column>
              <cv-multi-select
                :label="$t('webhooks.specific_mailboxes')"
                v-model="webhookForm.trigger_config.mailboxes"
                :options="mailboxOptions"
                :placeholder="$t('webhooks.all_mailboxes')"
                :disabled="loading"
                filterable
              ></cv-multi-select>
            </cv-column>
          </cv-row>
        </template>
      </cv-accordion-item>
    </cv-accordion>

    <!-- Mail Filters Configuration -->
    <cv-accordion style="margin-top: 1rem;">
      <cv-accordion-item>
        <template slot="title">{{
          $t("webhooks.mail_filters")
        }}</template>
        <template slot="content">
          <cv-row>
            <cv-column :md="6">
              <cv-text-area
                :label="$t('webhooks.sender_patterns')"
                v-model="senderPatternsText"
                :placeholder="$t('webhooks.sender_patterns_placeholder')"
                :disabled="loading"
                rows="3"
              ></cv-text-area>
            </cv-column>
            <cv-column :md="6">
              <cv-text-area
                :label="$t('webhooks.subject_patterns')"
                v-model="subjectPatternsText"
                :placeholder="$t('webhooks.subject_patterns_placeholder')"
                :disabled="loading"
                rows="3"
              ></cv-text-area>
            </cv-column>
          </cv-row>
          
          <cv-row>
            <cv-column>
              <cv-text-area
                :label="$t('webhooks.body_patterns')"
                v-model="bodyPatternsText"
                :placeholder="$t('webhooks.body_patterns_placeholder')"
                :disabled="loading"
                rows="3"
              ></cv-text-area>
            </cv-column>
          </cv-row>
          
          <cv-row>
            <cv-column :md="4">
              <cv-dropdown
                :label="$t('webhooks.has_attachments')"
                v-model="webhookForm.mail_filters.has_attachments"
                :disabled="loading"
              >
                <cv-dropdown-item :value="null">
                  {{ $t("webhooks.any") }}
                </cv-dropdown-item>
                <cv-dropdown-item :value="true">
                  {{ $t("webhooks.with_attachments") }}
                </cv-dropdown-item>
                <cv-dropdown-item :value="false">
                  {{ $t("webhooks.without_attachments") }}
                </cv-dropdown-item>
              </cv-dropdown>
            </cv-column>
            <cv-column :md="4">
              <cv-text-input
                :label="$t('webhooks.min_size_kb')"
                v-model.number="webhookForm.mail_filters.min_size_kb"
                :placeholder="'0'"
                :disabled="loading"
                type="number"
                min="0"
              ></cv-text-input>
            </cv-column>
            <cv-column :md="4">
              <cv-text-input
                :label="$t('webhooks.max_size_kb')"
                v-model.number="webhookForm.mail_filters.max_size_kb"
                :placeholder="'10240'"
                :disabled="loading"
                type="number"
                min="0"
              ></cv-text-input>
            </cv-column>
          </cv-row>
        </template>
      </cv-accordion-item>
    </cv-accordion>

    <!-- Post-Processing Actions -->
    <cv-accordion style="margin-top: 1rem;">
      <cv-accordion-item>
        <template slot="title">{{
          $t("webhooks.post_actions")
        }}</template>
        <template slot="content">
          <cv-row>
            <cv-column :md="6">
              <cv-checkbox
                :label="$t('webhooks.mark_as_read')"
                v-model="webhookForm.post_actions.mark_as_read"
                :disabled="loading"
              ></cv-checkbox>
              
              <cv-checkbox
                :label="$t('webhooks.delete_message')"
                v-model="webhookForm.post_actions.delete_message"
                :disabled="loading"
              ></cv-checkbox>
            </cv-column>
            <cv-column :md="6">
              <cv-text-input
                :label="$t('webhooks.move_to_folder')"
                v-model="webhookForm.post_actions.move_to_folder"
                :placeholder="$t('webhooks.move_to_folder_placeholder')"
                :disabled="loading"
              ></cv-text-input>
              
              <cv-text-input
                :label="$t('webhooks.add_flag')"
                v-model="webhookForm.post_actions.add_flag"
                :placeholder="$t('webhooks.add_flag_placeholder')"
                :disabled="loading"
              ></cv-text-input>
            </cv-column>
          </cv-row>
        </template>
      </cv-accordion-item>
    </cv-accordion>
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
        trigger_config: {
          trigger_type: "realtime",
          mailboxes: [],
          interval_seconds: 300,
        },
        mail_filters: {
          sender_patterns: [],
          subject_patterns: [],
          body_patterns: [],
          has_attachments: null,
          min_size_kb: null,
          max_size_kb: null,
        },
        post_actions: {
          mark_as_read: false,
          delete_message: false,
          move_to_folder: "",
          add_flag: "",
        },
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
      mailboxOptions: [], // Will be populated from mail server
      validationErrors: {
        name: "",
        url: "",
        api_key: "",
        interval_seconds: "",
        mailboxes: "",
        filters: "",
      },
    };
  },
  computed: {
    // Legacy support - map trigger_type to trigger_config
    webhookFormProxy: {
      get() {
        return {
          ...this.webhookForm,
          trigger_type: this.webhookForm.trigger_config?.trigger_type || 'realtime',
          interval: this.webhookForm.trigger_config?.interval_seconds || 300,
        };
      },
      set(value) {
        // Update trigger_config when legacy fields are modified
        if (!this.webhookForm.trigger_config) {
          this.webhookForm.trigger_config = {};
        }
        
        if (value.trigger_type !== undefined) {
          this.webhookForm.trigger_config.trigger_type = value.trigger_type;
        }
        
        if (value.interval !== undefined) {
          this.webhookForm.trigger_config.interval_seconds = value.interval;
        }
        
        Object.assign(this.webhookForm, value);
        this.emitUpdate();
      }
    },
    
    senderPatternsText: {
      get() {
        return this.webhookForm.mail_filters?.sender_patterns?.join('\n') || '';
      },
      set(value) {
        if (!this.webhookForm.mail_filters) {
          this.webhookForm.mail_filters = {};
        }
        this.webhookForm.mail_filters.sender_patterns = value
          ? value.split('\n').filter(line => line.trim())
          : [];
        this.emitUpdate();
      },
    },
    
    subjectPatternsText: {
      get() {
        return this.webhookForm.mail_filters?.subject_patterns?.join('\n') || '';
      },
      set(value) {
        if (!this.webhookForm.mail_filters) {
          this.webhookForm.mail_filters = {};
        }
        this.webhookForm.mail_filters.subject_patterns = value
          ? value.split('\n').filter(line => line.trim())
          : [];
        this.emitUpdate();
      },
    },
    
    bodyPatternsText: {
      get() {
        return this.webhookForm.mail_filters?.body_patterns?.join('\n') || '';
      },
      set(value) {
        if (!this.webhookForm.mail_filters) {
          this.webhookForm.mail_filters = {};
        }
        this.webhookForm.mail_filters.body_patterns = value
          ? value.split('\n').filter(line => line.trim())
          : [];
        this.emitUpdate();
      },
    },
    
    mailboxesText: {
      get() {
        return Array.isArray(this.webhookForm.trigger_config?.mailboxes)
          ? this.webhookForm.trigger_config.mailboxes.join("\n")
          : "";
      },
      set(value) {
        if (!this.webhookForm.trigger_config) {
          this.webhookForm.trigger_config = {};
        }
        this.webhookForm.trigger_config.mailboxes = value
          ? value.split("\n").filter((line) => line.trim())
          : [];
        this.emitUpdate();
      },
    },
    filtersText: {
      get() {
        try {
          return JSON.stringify(this.webhookForm.mail_filters, null, 2);
        } catch {
          return "";
        }
      },
      set(value) {
        try {
          this.webhookForm.mail_filters = value ? JSON.parse(value) : {};
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
      if (this.webhookForm.trigger_config?.trigger_type === "interval") {
        const intervalSeconds = this.webhookForm.trigger_config?.interval_seconds;
        if (!intervalSeconds || intervalSeconds < 60) {
          this.validationErrors.interval_seconds = this.$t("webhooks.invalid_interval_min");
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
