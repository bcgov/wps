import React from 'react'
import { CssBaseline } from '@mui/material'
import { ThemeProvider, Theme, StyledEngineProvider } from '@mui/material/styles'

import { theme } from 'app/theme'
import WPSRoutes from 'app/Routes'

declare module '@mui/styles/defaultTheme' {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface DefaultTheme extends Theme {}
}

const App: React.FunctionComponent = () => {
  return (
    <React.StrictMode>
      <StyledEngineProvider injectFirst>
        <CssBaseline />
        <ThemeProvider theme={theme}>
          <WPSRoutes />
        </ThemeProvider>
      </StyledEngineProvider>
    </React.StrictMode>
  )
}

export default React.memo(App)
