import { createApp } from 'vue'
import './theme.css'
import App from '/src/App.vue'
import vuetify from './plugins/vuetify';
import router from './router'
import store from './store'

import { loadFonts } from './plugins/webfontloader'

loadFonts()

createApp(App).use(store).use(router)
    .use(vuetify)
    .use(require('vue3-shortkey'))
    .mount('#app')
