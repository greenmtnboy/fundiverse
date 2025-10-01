import { createApp } from "vue";
import "./theme.css";
import App from "/src/App.vue";
import vuetify from "./plugins/vuetify";
import router from "./router";
import store from "./store";
import 'prismjs/plugins/line-numbers/prism-line-numbers.css'
import 'prismjs'
import 'prismjs/components/prism-sql'
import { createPinia } from 'pinia'
import { loadFonts } from "./plugins/webfontloader";

loadFonts();
const pinia = createPinia()

createApp(App)
  .use(store)
  .use(router)
  .use(vuetify)
  .use(pinia)
  .use(require("vue3-shortkey"))
  .mount("#app");
