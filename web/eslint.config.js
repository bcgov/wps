import js from '@eslint/js'
import { fixupConfigRules, fixupPluginRules } from '@eslint/compat'
import { FlatCompat } from '@eslint/eslintrc'
import tsParser from '@typescript-eslint/parser'
import typescriptEslint from '@typescript-eslint/eslint-plugin'
import globals from 'globals'
import path from 'node:path'
import prettier from 'eslint-plugin-prettier'
import react from 'eslint-plugin-react'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const srcFiles = ['src/**/*.{ts,tsx}']

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all
})

const compatConfigs = compat
  .extends(
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:@typescript-eslint/eslint-recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:prettier/recommended'
  )
  .map(config => ({
    ...config,
    files: srcFiles
  }))

export default [
  {
    ignores: ['src/serviceWorker.ts', 'src/**/__tests__/**/*', 'src/**/*.stories.tsx', 'src/types/**/*', '**/cypress/']
  },
  ...fixupConfigRules(compatConfigs),
  {
    files: srcFiles,
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
      'react/react-in-jsx-scope': 'off',
      'react/jsx-uses-react': 'off',
      'no-useless-catch': 'off',
      '@typescript-eslint/ban-ts-comment': 'warn',
      '@typescript-eslint/camelcase': 'off',
      '@typescript-eslint/explicit-function-return-type': 'off'
    }
  }
]
