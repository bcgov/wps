import React from 'react'
import { CssBaseline } from '@material-ui/core'
import { ThemeProvider, createMuiTheme } from '@material-ui/core/styles'

import { FWICalculatorPage } from 'features/fwiCalculator/FWICalculatorPage'

// Theme documentation: https://material-ui.com/customization/palette/
// Theme demo: https://material.io/resources/color/#!/?view.left=1&view.right=1&primary.color=003365&secondary.color=FBC02D
// Do not export this! theme can be accessed within makeStyles & withStyles. Use ErrorMessage.tsx as a reference
const theme = createMuiTheme({
  palette: {
    primary: {
      light: '#3E5C93',
      main: '#003365',
      dark: '#000C3A'
    },
    secondary: {
      light: '#FFF263',
      main: '#FBC02D',
      dark: '#C49000'
    },
    success: { main: '#44D77A' },
    error: { main: '#FF3E34' },
    warning: { main: '#FE7921' },
    contrastThreshold: 3,
    tonalOffset: 0.1
  },
  typography: {
    button: {
      textTransform: 'none'
    }
  }
})

const App = () => {
  return (
    <>
      <CssBaseline />
      <ThemeProvider theme={theme}>
        <FWICalculatorPage />
      </ThemeProvider>
    </>
  )
}

export default App
