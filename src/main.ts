import { createApp } from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import VueVirtualScroller from 'vue-virtual-scroller';
import { loadFonts } from './plugins/webfontloader'
import router from './router'
import store from './store'


loadFonts()

// const localStore = new Store<Record<string, string>>({
//   name: 'login-encrypted',
// //   watch: true,
//   encryptionKey: 'this_is_always_accessible_by_user',
// });


createApp(App).use(store).use(router)
  .use(vuetify)
  // .use(VueVirtualScroller)
  .mount('#app')
