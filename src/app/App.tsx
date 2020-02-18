import React from 'react'
import { Container, CssBaseline } from '@material-ui/core'
import { ThemeProvider } from '@material-ui/core/styles'
import theme from 'app/theme'

const App = () => {
  return (
    <>
      <CssBaseline />
      <ThemeProvider theme={theme}>
        <Container maxWidth="md">Hello World!</Container>
      </ThemeProvider>
    </>
  )
}

export default App
