<!--
  Copyright (C) 2023 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <div class="mail-webhooks-container">
    <AppLoader v-if="loading.page" />
    <div v-else class="mail-webhooks-content">
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
import axios from "axios";
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
  methods: {    async loadMailboxes() {
      this.loading.mailboxes = true;
      this.loading.page = true;
      
      try {
        const res = await axios.get('/api/mailboxes');
        this.mailboxes = res.data.mailboxes || [];
      } catch (error) {
        console.error('Error loading mailboxes:', error);
        this.createErrorNotificationForApp(
          error,
          this.$t("mail_webhooks.error_loading_mailboxes") || "Failed to load mailboxes"
        );
        this.mailboxes = [];
      }
      
      this.loading.page = false;
      this.loading.mailboxes = false;
    },
  },
};
</script>

<style scoped lang="scss">
@import "@/styles/carbon-utils";

.mail-webhooks-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.mail-webhooks-content {
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
}

.page-title {
  margin-bottom: 1rem;
}

.page-title h2 {
  margin: 0;
  font-weight: 400;
}
</style>
