module.exports = {
  // create react app wants to run eslint itself. but since our ci is always running it anyway
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
