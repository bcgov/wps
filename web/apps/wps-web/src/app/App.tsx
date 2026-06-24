import { CssBaseline } from '@mui/material'
import { StyledEngineProvider, ThemeProvider } from '@mui/material/styles'
import { LicenseInfo } from '@mui/x-license'
import { theme } from '@wps/ui/theme'
import { MUI_LICENSE } from '@wps/utils/env'
import WPSRoutes from 'app/Routes'
import React from 'react'

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
