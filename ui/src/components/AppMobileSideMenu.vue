<!--
  Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <transition name="slide-menu">
    <div
      v-if="isMenuShown"
      class="
        mobile-side-menu
        cv-side-nav
        bx--side-nav bx--side-nav__navigation
        bx--side-nav--expanded
        app-side-nav
      "
    >
      <AppSideMenuContent />
    </div>
  </transition>
</template>

<script>
import AppSideMenuContent from "@/components/AppSideMenuContent";

export default {
  name: "AppMobileSideMenu",
  components: { AppSideMenuContent },
  data() {
    return {
      isMenuShown: false,
      isClickOutsideEnabled: false,
    };
  },
  created() {
    // register to logout event
    this.$root.$on("toggleMobileSideMenu", this.toggleMobileSideMenu);
  },
  mounted() {
    // prevent glitch: click-outside is incorrectly detected when mobile side menu appears
    setTimeout(() => {
      this.isClickOutsideEnabled = true;
    }, 200);
  },
  beforeDestroy() {
    // remove event listener
    this.$root.$off("toggleMobileSideMenu");
  },
  methods: {
    toggleMobileSideMenu() {
      this.isMenuShown = !this.isMenuShown;
    },
    clickOutside() {
      if (this.isClickOutsideEnabled) {
        this.isMenuShown = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.mobile-side-menu {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 9999;
  background: white;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  max-width: 16rem;
  width: 100%;
}

.slide-menu-enter-active,
.slide-menu-leave-active {
  transition: transform 0.3s ease;
}

.slide-menu-enter,
.slide-menu-leave-to {
  transform: translateX(-100%);
}
</style>
