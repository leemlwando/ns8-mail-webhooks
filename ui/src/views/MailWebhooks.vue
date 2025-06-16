<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <div>
    <AppLoader v-if="loading.page" />
    <div v-else>
      <div class="page-title">
        <h2>{{ $t("mail_webhooks.title") }}</h2>
      </div>
      
      <cv-tabs aria-label="Mail webhook management tabs">
        <cv-tab
          id="scheduled-triggers-tab"
          :label="$t('mail_webhooks.scheduled_triggers')"
        >
          <ScheduledTriggers 
            :mailboxes="mailboxes"
            :loading="loading"
            @refresh-mailboxes="loadMailboxes"
          />
        </cv-tab>
        <cv-tab
          id="one-time-job-tab"
          :label="$t('mail_webhooks.one_time_job')"
        >
          <OneTimeJob 
            :mailboxes="mailboxes"
            :loading="loading"
            @refresh-mailboxes="loadMailboxes"
          />
        </cv-tab>
      </cv-tabs>
    </div>
  </div>
</template>

<script>
import { UtilService, TaskService, IconService } from "@nethserver/ns8-ui-lib";
import to from "await-to-js";
import ScheduledTriggers from "@/components/ScheduledTriggers";
import OneTimeJob from "@/components/OneTimeJob";

export default {
  name: "MailWebhooks",
  components: {
    ScheduledTriggers,
    OneTimeJob,
  },
  mixins: [UtilService, TaskService, IconService],
  data() {
    return {
      loading: {
        page: true,
        mailboxes: false,
      },
      mailboxes: [],
    };
  },
  created() {
    this.loadMailboxes();
  },
  methods: {
    async loadMailboxes() {
      this.loading.mailboxes = true;
      this.loading.page = true;
      
      const taskAction = "list-user-mailboxes";
      const eventId = this.getUuid();

      // register to task error
      this.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.loadMailboxesAborted
      );

      // register to task completion
      this.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.loadMailboxesCompleted
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
        this.createErrorNotificationForApp(
          err,
          this.$t("task.cannot_create_task", { action: taskAction })
        );
        this.loading.page = false;
        this.loading.mailboxes = false;
        return;
      }
    },
    loadMailboxesAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.loading.page = false;
      this.loading.mailboxes = false;
    },
    loadMailboxesCompleted(taskContext, taskResult) {
      this.mailboxes = taskResult.output.mailboxes || [];
      this.loading.page = false;
      this.loading.mailboxes = false;
    },
  },
};
</script>

<style scoped lang="scss">
.page-title {
  margin-bottom: $spacing-05;
}

.page-title h2 {
  margin: 0;
  font-weight: 400;
}
</style>
