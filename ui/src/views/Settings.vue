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
      <cv-column>
        <cv-tile light>
          <cv-form @submit.prevent="configureModule">
            <cv-text-input
              :label="$t('settings.mongodb_url')"
              v-model="mongodbUrl"
              :placeholder="$t('settings.mongodb_url_placeholder')"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.mongodbUrl"
              ref="mongodbUrl"
            ></cv-text-input>

            <cv-text-input
              :label="$t('settings.webhooks_collection')"
              v-model="webhooksCollection"
              :placeholder="$t('settings.webhooks_collection_placeholder')"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.webhooksCollection"
              ref="webhooksCollection"
            ></cv-text-input>

            <cv-text-input
              :label="$t('settings.jobs_collection')"
              v-model="jobsCollection"
              :placeholder="$t('settings.jobs_collection_placeholder')"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.jobsCollection"
              ref="jobsCollection"
            ></cv-text-input>

            <cv-text-input
              :label="$t('settings.logs_collection')"
              v-model="logsCollection"
              :placeholder="$t('settings.logs_collection_placeholder')"
              :disabled="loading.getConfiguration || loading.configureModule"
              :invalid-message="error.logsCollection"
              ref="logsCollection"
            ></cv-text-input>
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
  },
  data() {
    return {
      q: {
        page: "settings",
      },
      urlCheckInterval: null,
      mongodbUrl: "",
      webhooksCollection: "webhooks",
      jobsCollection: "jobs",
      logsCollection: "logs",
      loading: {
        getConfiguration: false,
        configureModule: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        mongodbUrl: "",
        webhooksCollection: "",
        jobsCollection: "",
        logsCollection: "",
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
    },
    getConfigurationCompleted(taskContext, taskResult) {
      this.loading.getConfiguration = false;
      const config = taskResult.output;

      // Set configuration fields
      this.mongodbUrl = config.mongodb_url || "";
      this.webhooksCollection = config.webhooks_collection || "webhooks";
      this.jobsCollection = config.jobs_collection || "jobs";
      this.logsCollection = config.logs_collection || "logs";

      console.log("config", config);

      // Focus first configuration field
      this.focusElement("mongodbUrl");
    },
    validateConfigureModule() {
      this.clearErrors(this);
      let isValidationOk = true;

      // Validate MongoDB URL
      if (!this.mongodbUrl) {
        this.error.mongodbUrl = this.$t("common.required");
        if (isValidationOk) {
          this.focusElement("mongodbUrl");
          isValidationOk = false;
        }
      } else if (!this.isValidMongoUrl(this.mongodbUrl)) {
        this.error.mongodbUrl = this.$t("settings.invalid_mongodb_url");
        if (isValidationOk) {
          this.focusElement("mongodbUrl");
          isValidationOk = false;
        }
      }

      // Validate webhooks collection name
      if (!this.webhooksCollection) {
        this.error.webhooksCollection = this.$t("common.required");
        if (isValidationOk) {
          this.focusElement("webhooksCollection");
          isValidationOk = false;
        }
      } else if (!this.isValidCollectionName(this.webhooksCollection)) {
        this.error.webhooksCollection = this.$t(
          "settings.invalid_collection_name"
        );
        if (isValidationOk) {
          this.focusElement("webhooksCollection");
          isValidationOk = false;
        }
      }

      // Validate jobs collection name
      if (!this.jobsCollection) {
        this.error.jobsCollection = this.$t("common.required");
        if (isValidationOk) {
          this.focusElement("jobsCollection");
          isValidationOk = false;
        }
      } else if (!this.isValidCollectionName(this.jobsCollection)) {
        this.error.jobsCollection = this.$t("settings.invalid_collection_name");
        if (isValidationOk) {
          this.focusElement("jobsCollection");
          isValidationOk = false;
        }
      }

      // Validate logs collection name
      if (!this.logsCollection) {
        this.error.logsCollection = this.$t("common.required");
        if (isValidationOk) {
          this.focusElement("logsCollection");
          isValidationOk = false;
        }
      } else if (!this.isValidCollectionName(this.logsCollection)) {
        this.error.logsCollection = this.$t("settings.invalid_collection_name");
        if (isValidationOk) {
          this.focusElement("logsCollection");
          isValidationOk = false;
        }
      }

      // Check for duplicate collection names
      const collections = [
        this.webhooksCollection,
        this.jobsCollection,
        this.logsCollection,
      ];
      const uniqueCollections = [...new Set(collections)];
      if (collections.length !== uniqueCollections.length) {
        this.error.webhooksCollection = this.$t(
          "settings.duplicate_collection_names"
        );
        if (isValidationOk) {
          this.focusElement("webhooksCollection");
          isValidationOk = false;
        }
      }

      return isValidationOk;
    },

    isValidMongoUrl(url) {
      // Validate MongoDB connection strings (both mongodb:// and mongodb+srv://)
      const mongoUrlPattern = /^mongodb(\+srv)?:\/\/[^\s]+$/;
      return mongoUrlPattern.test(url);
    },

    isValidCollectionName(name) {
      // MongoDB collection names must start with letter or underscore
      // and contain only letters, numbers, and underscores
      const collectionNamePattern = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
      return collectionNamePattern.test(name) && name.length <= 64;
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
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            mongodb_url: this.mongodbUrl,
            webhooks_collection: this.webhooksCollection,
            jobs_collection: this.jobsCollection,
            logs_collection: this.logsCollection,
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
