import { defineClientConfig } from "@vuepress/client";
// Styles
// import '@mdi/font/css/materialdesignicons.css'
import '@mdi/font/css/materialdesignicons.css'
import "vuetify/styles";
// import Vuetify from 'vuetify'
// Vuetify
import { aliases, mdi } from 'vuetify/iconsets/mdi-svg'
import { createVuetify } from "vuetify";
import {
  VAlert,
  VBanner,
  VBannerText,
  VCard,
  VCardTitle,
  VIcon,
  VBtn,
  VProgressLinear,
  VChip,
  VChipGroup,
  VTabs,
  VSkeletonLoader,
  VTab,
  VList,
  VListItem,
  VTooltip,
  VTextField,
  VSwitch,
  VBtnToggle,
  VInput,
  VSelect,
  VCardText,
  VCardActions,
  VCardSubtitle,
  VDivider,
  VCol,
  VRow,
} from "vuetify/components";
import * as directives from "vuetify/directives";
import { store } from "./components/stores/index";
import { aliases, mdi } from 'vuetify/iconsets/mdi-svg'


export default defineClientConfig({
  enhance({ app, router, siteData }) {
    app.use(createVuetify({ icons: {
      defaultSet: 'mdi',
      aliases,
      sets: {
        mdi,
      },
    },}));
    app.use(store);
    app.component("VAlert", VAlert);
    app.component("VCard", VCard);
    app.component("VCardText", VCardText);
    app.component("VCardTitle", VCardTitle);
    app.component("VCol", VCol);
    app.component("VRow", VRow);
    app.component("VList", VList);
    app.component("VListItem", VListItem);
    app.component("VTooltip", VTooltip);
    app.component("VDivider", VDivider);
    app.component("VCardActions", VCardActions);
    app.component("VCardSubtitle", VCardSubtitle);
    app.component("VSelect", VSelect);
    app.component("VInput", VInput);
    app.component("VToggle", VBtnToggle);
    app.component("VSwitch", VSwitch);
    app.component("VTextField", VTextField);
    app.component("VTab", VTab);
    app.component("VTabs", VTabs);
    app.component("VChip", VChip);
    app.component("VChipGroup", VChipGroup);
    app.component("VSkeletonLoader", VSkeletonLoader);
    app.component("VProgressLinear", VProgressLinear);
    app.component("VBtn", VBtn);
    app.component("VIcon", VIcon);
    app.component("VBanner", VBanner);
    app.component("VBannerText", VBannerText);
    // app.component("VSelectItem", VSelectItem)
  },
  setup() {}, 
  layouts: {},
  rootComponents: [],
});
