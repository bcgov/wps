import React from 'react'
import { Button } from '@mui/material'
import { createTheme, ThemeProvider } from '@mui/material/styles'

const SignoutButton = () => {
  const theme = createTheme({
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            color: 'white',
            borderColor: 'white !important',
            textTransform: 'none'
          }
        }
      }
    }
  })

  return (
    <ThemeProvider theme={theme}>
      <React.Fragment>
        <Button
          variant="outlined"
          color="primary"
          onClick={() => {
            /**noop */
          }}
          data-testid={'sign-out-button'}
        >
          Sign out
        </Button>
      </React.Fragment>
    </ThemeProvider>
  )
}

export default React.memo(SignoutButton)
