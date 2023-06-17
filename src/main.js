import { createApp } from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import { loadFonts } from './plugins/webfontloader'
import router from './router'
import store from './store'

loadFonts()

createApp(App).use(store).use(router)
  .use(vuetify)
  .mount('#app')
