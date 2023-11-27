const { description } = require('../../package')

module.exports = {
  /**
   * Ref：https://v1.vuepress.vuejs.org/config/#title
   */
  title: 'Fundiverse',
  /**
   * Ref：https://v1.vuepress.vuejs.org/config/#description
   */
  description: description,

  /**
   * Extra tags to be injected to the page HTML `<head>`
   *
   * ref：https://v1.vuepress.vuejs.org/config/#head
   */
  head: [
    ['link', { rel: "apple-touch-icon", sizes: "180x180", href: "/favicon.png"}],
    ['meta', { name: 'theme-color', content: '#3eaf7c' }],
    ['meta', { name: 'apple-mobile-web-app-capable', content: 'yes' }],
    ['meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black' }],
    ['script', {
      async: true,
      src: 'https://www.googletagmanager.com/gtag/js?id=G-3P8R2SW79T'
  }],
    ['script', {}, `window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());

gtag('config', 'G-3P8R2SW79T');
`],
  ],

  /**
   * Theme configuration, here is the default theme configuration for VuePress.
   *
   * ref：https://v1.vuepress.vuejs.org/theme/default-theme-config.html
   */
  theme: "vt",
  themeConfig: {
    enableDarkMode: true,
    repo: 'https://github.com/greenmtnboy/fundiverse',
    editLinks: false,
    docsDir: '',
    editLinkText: '',
    lastUpdated: false,
    logo: '/logo-only-transparent-png.png',
    nav: [
      {
        text: 'Get Started',
        link: '/install/',
      },
      {
        text: 'About',
        link: '/about/'
      },
      // {
      //   text: 'VuePress',
      //   link: 'https://v1.vuepress.vuejs.org'
      // }
    ],
    sidebar: {
      '/install/': [
        {
          title: 'Overview',
          path: 'install',
          collapsable: false,
        },
        {
          title: 'Windows',
          path: 'windows',
          collapsable: false,
        },
        {
          title: 'Mac',
          path: 'mac',
          collapsable: false,
        },
        {
          title: 'Linux',
          path: 'linux',
          collapsable: false,
        },
        {
          title: 'First Portfolio',
          path: 'first-portfolio',
          collapsable: false,
        }
      ],
    }
  },

  /**
   * Apply plugins，ref：https://v1.vuepress.vuejs.org/zh/plugin/
   */
  plugins: [
    '@vuepress/plugin-back-to-top',
    '@vuepress/plugin-medium-zoom',
  ]
}
