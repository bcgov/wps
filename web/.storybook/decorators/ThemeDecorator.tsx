import React from 'react'
import { ThemeProvider } from '@material-ui/core/styles'

import { theme } from '../../src/app/theme'

/**
 * Storybook should now be wrapping all stories with this custom decorator,
 * which provides the custom theme configured for Material UI
 */
export const ThemeDecorator = storyFn => (
  <ThemeProvider theme={theme}>{storyFn()}</ThemeProvider>
)
