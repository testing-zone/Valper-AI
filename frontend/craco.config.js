module.exports = {
  devServer: {
    allowedHosts: "all",
    host: "0.0.0.0",
    port: 3000,
    client: {
      webSocketURL: "auto://0.0.0.0:0/ws"
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