import React from 'react'
import { CssBaseline } from '@material-ui/core'
import { ThemeProvider } from '@material-ui/core/styles'

import { Routes } from 'app/Routes'
import { theme } from 'app/theme'

const App = () => {
  return (
    <React.StrictMode>
      <CssBaseline />
      <ThemeProvider theme={theme}>
        <Routes />
      </ThemeProvider>
    </React.StrictMode>
  )
}

export default App
