<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("settings.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getConfiguration">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-configuration')"
          :description="error.getConfiguration"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>        <cv-tile light>
          <cv-form @submit.prevent="configureModule">
            <!-- MongoDB Configuration -->
            <cv-text-input
              :label="$t('settings.mongodb_url')"
              v-model="mongodb_url"
              :placeholder="$t('settings.mongodb_url_placeholder')"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.mongodb_url"
              ref="mongodb_url"
              type="password"
            ></cv-text-input>

            <!-- Mail Server UUID -->
            <cv-text-input
              :label="$t('settings.mail_server_uuid')"
              v-model="mail_server_uuid"
              :placeholder="$t('settings.mail_server_uuid_placeholder')"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.mail_server_uuid"
              ref="mail_server_uuid"
            ></cv-text-input>

            <!-- Collection Names Section -->
            <cv-accordion>
              <cv-accordion-item>
                <template slot="title">{{ $t('settings.collection_names') }}</template>
                <template slot="content">
                  <cv-row>
                    <cv-column>
                      <cv-text-input
                        :label="$t('settings.webhooks_collection')"
                        v-model="webhooks_collection"
                        :placeholder="'webhooks'"
                        :disabled="loading.getConfiguration || loading.configureModule"
                        :invalid-message="error.webhooks_collection"
                        ref="webhooks_collection"
                      ></cv-text-input>
                    </cv-column>
                    <cv-column>
                      <cv-text-input
                        :label="$t('settings.events_collection')"
                        v-model="events_collection"
                        :placeholder="'events'"
                        :disabled="loading.getConfiguration || loading.configureModule"
                        :invalid-message="error.events_collection"
                        ref="events_collection"
                      ></cv-text-input>
                    </cv-column>
                  </cv-row>
                  <cv-row>
                    <cv-column>
                      <cv-text-input
                        :label="$t('settings.settings_collection')"
                        v-model="settings_collection"
                        :placeholder="'settings'"
                        :disabled="loading.getConfiguration || loading.configureModule"
                        :invalid-message="error.settings_collection"
                        ref="settings_collection"
                      ></cv-text-input>
                    </cv-column>
                    <cv-column>
                      <cv-text-input
                        :label="$t('settings.triggers_collection')"
                        v-model="triggers_collection"
                        :placeholder="'triggers'"
                        :disabled="loading.getConfiguration || loading.configureModule"
                        :invalid-message="error.triggers_collection"
                        ref="triggers_collection"
                      ></cv-text-input>
                    </cv-column>
                  </cv-row>
                  <cv-row>
                    <cv-column>
                      <cv-text-input
                        :label="$t('settings.logs_collection')"
                        v-model="logs_collection"
                        :placeholder="'logs'"
                        :disabled="loading.getConfiguration || loading.configureModule"
                        :invalid-message="error.logs_collection"
                        ref="logs_collection"
                      ></cv-text-input>
                    </cv-column>
                    <cv-column>
                      <!-- Empty column for layout balance -->
                    </cv-column>
                  </cv-row>                </template>
              </cv-accordion-item>
            </cv-accordion>

            <!-- Add spacing after advanced section -->
            <div style="margin-bottom: 2rem;"></div>

            <cv-row v-if="error.configureModule">
              <cv-column>
                <NsInlineNotification
                  kind="error"
                  :title="$t('action.configure-module')"
                  :description="error.configureModule"
                  :showCloseButton="false"
                />
              </cv-column>
            </cv-row>
            <NsButton
              kind="primary"
              :icon="Save20"
              :loading="loading.configureModule"
              :disabled="loading.getConfiguration || loading.configureModule"
              >{{ $t("settings.save") }}</NsButton
            >
          </cv-form>
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
  UtilService,
  TaskService,
  IconService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";

export default {
  name: "Settings",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    PageTitleService,
  ],
  pageTitle() {
    return this.$t("settings.title") + " - " + this.appName;
  },  data() {
    return {
      q: {
        page: "settings",
      },
      urlCheckInterval: null,
      mongodb_url: "",
      mail_server_uuid: "",
      webhooks_collection: "webhooks",
      events_collection: "events",
      settings_collection: "settings",
      triggers_collection: "triggers",
      logs_collection: "logs",
      loading: {
        getConfiguration: false,
        configureModule: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        mongodb_url: "",
        mail_server_uuid: "",
        webhooks_collection: "",
        events_collection: "",
        settings_collection: "",
        triggers_collection: "",
        logs_collection: "",
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
    this.getConfiguration();
  },
  methods: {
    async getConfiguration() {
      this.loading.getConfiguration = true;
      this.error.getConfiguration = "";
      const taskAction = "get-configuration";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.getConfigurationAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.getConfigurationCompleted
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
        this.error.getConfiguration = this.getErrorMessage(err);
        this.loading.getConfiguration = false;
        return;
      }
    },
    getConfigurationAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.getConfiguration = this.$t("error.generic_error");
      this.loading.getConfiguration = false;
    },    getConfigurationCompleted(taskContext, taskResult) {
      this.loading.getConfiguration = false;
      const config = taskResult.output;

      // Set configuration fields
      this.mongodb_url = config.mongodb_url || "";
      this.mail_server_uuid = config.mail_server_uuid || "";
      this.webhooks_collection = config.webhooks_collection || "webhooks";
      this.events_collection = config.events_collection || "events";
      this.settings_collection = config.settings_collection || "settings";
      this.triggers_collection = config.triggers_collection || "triggers";
      this.logs_collection = config.logs_collection || "logs";

      console.log("config", config);

      // Focus first configuration field
      this.focusElement("mongodb_url");
    },    validateConfigureModule() {
      this.clearErrors(this);
      let isValidationOk = true;

      // MongoDB URL is required
      if (!this.mongodb_url) {
        this.error.mongodb_url = this.$t("common.required");
        if (isValidationOk) {
          this.focusElement("mongodb_url");
          isValidationOk = false;
        }
      } else if (!this.mongodb_url.startsWith("mongodb://") && !this.mongodb_url.startsWith("mongodb+srv://")) {
        this.error.mongodb_url = this.$t("settings.invalid_mongodb_url");
        if (isValidationOk) {
          this.focusElement("mongodb_url");
          isValidationOk = false;
        }
      }

      // Validate collection names (must be valid MongoDB collection names)
      const collectionNamePattern = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
      const collections = [
        { field: 'webhooks_collection', value: this.webhooks_collection },
        { field: 'events_collection', value: this.events_collection },
        { field: 'settings_collection', value: this.settings_collection },
        { field: 'triggers_collection', value: this.triggers_collection },
        { field: 'logs_collection', value: this.logs_collection }
      ];

      for (const collection of collections) {
        if (collection.value && !collectionNamePattern.test(collection.value)) {
          this.error[collection.field] = this.$t("settings.invalid_collection_name");
          if (isValidationOk) {
            this.focusElement(collection.field);
            isValidationOk = false;
          }
        }
      }

      return isValidationOk;
    },
    configureModuleValidationFailed(validationErrors) {
      this.loading.configureModule = false;
      let focusAlreadySet = false;

      for (const validationError of validationErrors) {
        const field = validationError.field;

        if (field !== "(root)") {
          // set i18n error message
          this.error[field] = this.$t("settings." + validationError.error);

          if (!focusAlreadySet) {
            this.focusElement(field);
            focusAlreadySet = true;
          }
        }
      }
    },
    async configureModule() {
      const isValidationOk = this.validateConfigureModule();
      if (!isValidationOk) {
        return;
      }

      this.loading.configureModule = true;
      const taskAction = "configure-module";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.configureModuleAborted
      );

      // register to task validation
      this.core.$root.$once(
        `${taskAction}-validation-failed-${eventId}`,
        this.configureModuleValidationFailed
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.configureModuleCompleted
      );      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            mongodb_url: this.mongodb_url,
            mail_server_uuid: this.mail_server_uuid || undefined,
            webhooks_collection: this.webhooks_collection || "webhooks",
            events_collection: this.events_collection || "events", 
            settings_collection: this.settings_collection || "settings",
            triggers_collection: this.triggers_collection || "triggers",
            logs_collection: this.logs_collection || "logs",
          },
          extra: {
            title: this.$t("settings.configure_instance", {
              instance: this.instanceName,
            }),
            description: this.$t("common.processing"),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.configureModule = this.getErrorMessage(err);
        this.loading.configureModule = false;
        return;
      }
    },
    configureModuleAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.configureModule = this.$t("error.generic_error");
      this.loading.configureModule = false;
    },
    configureModuleCompleted() {
      this.loading.configureModule = false;

      // reload configuration
      this.getConfiguration();
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";
</style>
