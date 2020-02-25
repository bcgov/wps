import React from 'react'
import { CssBaseline } from '@material-ui/core'
import { ThemeProvider } from '@material-ui/core/styles'

import theme from 'app/theme'
import { FWICalculatorPage } from 'features/fwiCalculator/FWICalculatorPage'

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
