<!--
Copyright (C) 2023 Lee M. Lwando <leemlwando@gmail.com>
SPDX-License-Identifier: MIT
-->
<template>
  <div class="webhooks-view">
    <cv-grid fullWidth>
      <cv-row>
        <cv-column>
          <h2 class="page-title">{{ $t("webhooks.title") }}</h2>
          <p class="page-description">
            {{ $t("webhooks.description") }}
          </p>
        </cv-column>
      </cv-row>
    </cv-grid>

    <cv-tabs aria-label="Webhook actions">
      <cv-tab id="tab-1" :label="$t('webhooks.scheduled_triggers')">
        <ScheduledTriggers />
      </cv-tab>
      <cv-tab id="tab-2" :label="$t('webhooks.run_one_time_job')">
        <OneTimeJob />
      </cv-tab>
    </cv-tabs>
  </div>
</template>

<script>
import ScheduledTriggers from "@/components/ScheduledTriggers.vue";
import OneTimeJob from "@/components/OneTimeJob.vue";

export default {
  name: "Webhooks",
  components: {
    ScheduledTriggers,
    OneTimeJob,
  },
  mounted() {
    // Set page title
    this.$nextTick(() => {
      this.$parent.title = this.$t("webhooks.title");
    });
  },
};
</script>

<style lang="scss" scoped>
.page-title {
  margin-bottom: 1rem;
  font-size: 2rem;
  font-weight: 400;
}

.page-description {
  margin-bottom: 2rem;
  color: var(--cds-text-02);
  font-size: 1rem;
  line-height: 1.5;
}

.webhooks-view {
  padding: 1rem;
}
</style>
