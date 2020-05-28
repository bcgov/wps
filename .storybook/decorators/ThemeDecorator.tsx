import React from 'react'
import { ThemeProvider } from '@material-ui/core/styles'

import { theme } from '../../src/app/theme'

export const ThemeDecorator = storyFn => (
  <ThemeProvider theme={theme}>{storyFn()}</ThemeProvider>
)
