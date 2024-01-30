import { defineClientConfig } from '@vuepress/client'
// Styles
// import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
// import Vuetify from 'vuetify'
// Vuetify
import { createVuetify } from 'vuetify'
import {VCard, VCardTitle, VChip, VChipGroup, VTabs, VTab, VList, VListItem, VTooltip, VTextField, VSwitch, VBtnToggle,VInput, VSelect, VCardText, VCardActions, VCardSubtitle, VDivider} from 'vuetify/components'
import * as directives from 'vuetify/directives'
import {store} from './components/stores/index'


export default defineClientConfig({
  enhance({ app, router, siteData }) {
    app.use(createVuetify());
    app.use(store);
    app.component("VCard", VCard);
    app.component("VCardText", VCardText);
    app.component("VCardTitle", VCardTitle);
    app.component("VList", VList);
    app.component("VListItem", VListItem);
    app.component("VTooltip", VTooltip);
    app.component("VDivider", VDivider);
    app.component("VCardActions", VCardActions);
    app.component("VSelect", VSelect);
    app.component("VInput", VInput);
    app.component("VToggle", VBtnToggle);
    app.component("VSwitch", VSwitch);
    app.component("VTextField", VTextField);
    app.component("VTab", VTab);
    app.component("VTabs", VTabs);
    app.component("VChip", VChip);
    app.component("VChipGroup", VChipGroup);
    // app.component("VSelectItem", VSelectItem)
    
  },
  setup() {},
  layouts: {},
  rootComponents: [],
});