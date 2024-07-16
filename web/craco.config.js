module.exports = {
  eslint: {
    enable: false
  },
  webpack: {
    configure: {
      module: {
        rules: [
          {
            test: /\.m?js$/,
            resolve: {
              fullySpecified: false
            }
          }
        ]
      }
    }
  }
}
