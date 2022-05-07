// eslint-disable-next-line @typescript-eslint/no-var-requires
const CracoSwcPlugin = require('craco-swc')
module.exports = {
  plugins: [
    {
      plugin: CracoSwcPlugin,
      options: {
        swcLoaderOptions: {
          jsc: {
            externalHelpers: true,
            target: 'es2015',
            parser: {
              syntax: 'typescript',
              tsx: true,
              decorators: true,
              dynamicImport: true
            }
          }
        }
      }
    }
  ]
}
