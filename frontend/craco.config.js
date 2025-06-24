module.exports = {
  devServer: {
    allowedHosts: "all",
    host: "0.0.0.0",
    port: 3000,
    client: {
      webSocketURL: "auto://0.0.0.0:0/ws"
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  webpack: {
    configure: (webpackConfig) => {
      // Disable source maps for development
      webpackConfig.devtool = false;
      return webpackConfig;
    }
  }
}; 