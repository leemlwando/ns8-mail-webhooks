//
// Copyright (C) 2023 Lee M. Lwando <leemlwando@gmail.com>
// SPDX-License-Identifier: MIT
//
import Vue from "vue";
import VueRouter from "vue-router";
import Webhooks from "../views/Webhooks.vue";
import Settings from "../views/Settings.vue";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "Webhooks",
    component: Webhooks,
    alias: "/webhooks", // important
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
