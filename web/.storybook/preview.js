import React from 'react'
import { ThemeProvider } from '@material-ui/core/styles'

import { theme } from '../src/app/theme'
import '../src/index.css'

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' }
}

/**
 * Storybook should now be wrapping all stories with this custom decorator,
 * which provides the custom theme configured for Material UI
 */
export const decorators = [
  Story => (
    <ThemeProvider theme={theme}>
      <Story />
    </ThemeProvider>
  )
]
