import { defineClientConfig } from '@vuepress/client'
// Styles
// import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
// import Vuetify from 'vuetify'
// Vuetify
import { createVuetify } from 'vuetify'
import {VCard, VCardTitle, VList, VListItem, VTooltip} from 'vuetify/components'
import * as directives from 'vuetify/directives'



export default defineClientConfig({
  enhance({ app, router, siteData }) {
    app.use(createVuetify());
    app.component("VCard", VCard);
    app.component("VCardTitle", VCardTitle);
    app.component("VList", VList);
    app.component("VListItem", VListItem);
    app.component("VTooltip", VTooltip);
    
  },
  setup() {},
  layouts: {},
  rootComponents: [],
});