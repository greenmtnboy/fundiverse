import { description } from "../../package";
import { getDirname, path } from "@vuepress/utils";
import { hopeTheme } from "vuepress-theme-hope";
import registerComponentsPlugin from "@vuepress/plugin-register-components";
import { viteBundler } from "@vuepress/bundler-vite";



const __dirname = getDirname(import.meta.url);

export default {
  /**
   * Ref：https://v1.vuepress.vuejs.org/config/#title
   */
  title: "Fundiverse",
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
    [
      "link",
      { rel: "apple-touch-icon", sizes: "180x180", href: "/favicon.png" },
    ],
    ["meta", { name: "theme-color", content: "#3eaf7c" }],
    ["meta", { name: "apple-mobile-web-app-capable", content: "yes" }],
    ['link', { rel: 'stylesheet', href: "https://cdn.jsdelivr.net/npm/@mdi/font@5.x/css/materialdesignicons.min.css" }],
    ['link', { rel: 'stylesheet', href: "https://fonts.googleapis.com/icon?family=Material+Icons" }],
    [
      "meta",
      { name: "apple-mobile-web-app-status-bar-style", content: "black" },
    ],
    [
      "script",
      {
        async: true,
        src: "https://www.googletagmanager.com/gtag/js?id=G-53FSTW9NTV",
      },
    ],
    [
      "script",
      {},
      `window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());

gtag('config', 'G-53FSTW9NTV');
`,
    ],
  ],

  /**
   * Theme configuration, here is the default theme configuration for VuePress.
   *
   * ref：https://v1.vuepress.vuejs.org/theme/default-theme-config.html
   */
  // theme: "vt",
  theme: hopeTheme({
    enableDarkMode: true,
    repo: "https://github.com/greenmtnboy/fundiverse",
    editLinks: false,
    docsDir: "",
    editLinkText: "",
    lastUpdated: false,
    mdEnhance: {
      components: true,
    },
    logo: "/logo-only-transparent-png.png",
    clientConfigFile: path.resolve(__dirname, "./client.ts"),
    displayFooter: true,
    contributors: false,
    meta: {
      contributors: false,
    },
    footer:
      'Not Stock Advice | GPL Licensed | Contributions Welcome | <a href="https://github.com/greenmtnboy/fundiverse">Source</a> | <a href="/tos/">Terms of Service</a> | <a href="/privacy/">Privacy Policy</a>',
    navbar: [
      {
        text: "About",
        link: "/about/",
      },
      {
        text: "Index Lab/Demo",
        link: "/index_demo/",
      },
      {
        text: "Install",
        link: "/install/",
      },
    ],
    sidebar: {
      "/install/":
        [
          {
            text: "Overview",
            link: "/install/",
          },
          {
            text: "Windows",
            link: "/install/windows",

          },
          {
            text: "Mac",
            link: "/install/mac",
          },
          {
            text: "Linux",
            link: "/install/linux",

          },
          {
            text: "First Portfolio",
            link: "/install/first-portfolio",
          },
          {
            text: "Alpaca",
            link: "/install/alpaca",
          },
          {
            text: "Robinhood",
            link: "/install/robinhood",
          },
          {
            text: "Webull",
            link: "/install/webull",
          },
          {
            text: "Schwab",
            link: "/install/schwab",
          },
        ],

    }
  },
  ),

  /**
   * Apply plugins，ref：https://v1.vuepress.vuejs.org/zh/plugin/
   */
  plugins: [
  ],
  bundler: viteBundler({
    viteOptions: {
      ssr: {
        noExternal: ["vuetify"],
      },
      optimizeDeps: {
        exclude: ["pyodide"],
      },
      plugins: [],
      resolve: {
        alias: {
          "node-fetch": "axios",
        },
      },
    },
    vuePluginOptions: {},
  }),
};
