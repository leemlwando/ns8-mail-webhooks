//
// Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
// SPDX-License-Identifier: GPL-3.0-or-later
//
import Vue from "vue";
import VueRouter from "vue-router";
import Status from "../views/Status.vue";
import Settings from "../views/Settings.vue";
import Webhooks from "../views/Webhooks.vue";
import ScheduledWebhooks from "../views/ScheduledWebhooks.vue";
import Logs from "../views/Logs.vue";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "Status",
    component: Status,
    alias: "/status", // important for NS8
  },
  {
    path: "/webhooks",
    name: "Webhooks",
    component: Webhooks,
  },
  {
    path: "/scheduled",
    name: "ScheduledWebhooks",
    component: ScheduledWebhooks,
  },
  {
    path: "/logs",
    name: "Logs",
    component: Logs,
  },
  {
    path: "/settings",
    name: "Settings",
    component: Settings,
  },
  {
    path: "/about",
    name: "About",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/About.vue"),
  },
];

const router = new VueRouter({
  base: process.env.BASE_URL,
  routes,
});

export default router;
