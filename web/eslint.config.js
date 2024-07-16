const { fixupConfigRules, fixupPluginRules } = require('@eslint/compat')
const typescriptEslint = require('@typescript-eslint/eslint-plugin')
const prettier = require('eslint-plugin-prettier')
const react = require('eslint-plugin-react')
const globals = require('globals')
const tsParser = require('@typescript-eslint/parser')
const js = require('@eslint/js')
const { FlatCompat } = require('@eslint/eslintrc')

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all
})

module.export = [
  {
    files: './src/**/*.{ts,tsx}'
  },
  {
    ignores: ['src/serviceWorker.ts', 'src/**/__tests__/**/*', 'src/**/*.stories.tsx', 'src/types/**/*', '**/cypress/']
  },
  ...fixupConfigRules(
    compat.extends(
      'eslint:recommended',
      'plugin:react/recommended',
      'plugin:react-hooks/recommended',
      'plugin:@typescript-eslint/eslint-recommended',
      'plugin:@typescript-eslint/recommended',
      'plugin:prettier/recommended'
    )
  ),
  {
    plugins: {
      '@typescript-eslint': fixupPluginRules(typescriptEslint),
      prettier: fixupPluginRules(prettier),
      react: fixupPluginRules(react)
    },
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.jasmine,
        ...globals.jest,
        ...globals.node,
        ...globals.commonjs
      },
      parser: tsParser
    },
    settings: {
      react: {
        pragma: 'React',
        version: 'detect'
      }
    },
    rules: {
      'prettier/prettier': [
        'error',
        {
          singleQuote: true,
          semi: false,
          printWidth: 120,
          trailingComma: 'none',
          arrowParens: 'avoid'
        }
      ],
      'react/prop-types': 'off',
      'no-useless-catch': 'off',
      '@typescript-eslint/ban-ts-comment': 'warn',
      '@typescript-eslint/camelcase': 'off',
      '@typescript-eslint/explicit-function-return-type': 'off'
    }
  }
]
