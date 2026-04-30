import React from 'react'
import { CssBaseline } from '@mui/material'
import { ThemeProvider, StyledEngineProvider } from '@mui/material/styles'
import { theme } from '@wps/ui/theme'
import WPSRoutes from 'app/Routes'
import { LicenseInfo } from '@mui/x-license'
import { MUI_LICENSE } from '@wps/utils/env'

LicenseInfo.setLicenseKey(MUI_LICENSE)

const App: React.FunctionComponent = () => {
  return (
    <StyledEngineProvider injectFirst>
      <CssBaseline />
      <ThemeProvider theme={theme}>
        <WPSRoutes />
      </ThemeProvider>
    </StyledEngineProvider>
  )
}

export default React.memo(App)
