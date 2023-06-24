const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack : {
    // plugins: [       new NodePolyfillPlugin(),     ],   },
    resolve: {
      fallback: {
        "os": false,
        "fs": false,
        "tls": false,
        "net": false,
        "path": false,
        "zlib": false,
        "http": false,
        "https": false,
        "stream": false,
        "crypto": false,
        "crypto-browserify": require.resolve('crypto-browserify'), //if you want to use this module also don't forget npm i crypto-browserify 
      } 
    },
    
  },
  pluginOptions: {
    vuetify: {
			// https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vuetify-loader
		},
    electronBuilder: {
      nodeIntegration: true,
      builderOptions: {
        publish: ['github'],
        extraResources: [
        {
          "from": "./src/background",
          "to": "src/background",
          "filter": "**/*"
        }]
      }
    }
  },

})
