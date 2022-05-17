import React from 'react'
import { Button } from '@mui/material'
import { createTheme, ThemeProvider } from '@mui/material/styles'
import { signout } from 'features/auth/slices/authenticationSlice'
import { AppDispatch } from 'app/store'
import { useDispatch } from 'react-redux'

const SignoutButton = () => {
  const dispatch: AppDispatch = useDispatch()

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
            try {
              dispatch(signout())
            } catch (err) {
              console.log('Error logging out: ', err)
            }
          }}
        >
          Sign out
        </Button>
      </React.Fragment>
    </ThemeProvider>
  )
}

export default React.memo(SignoutButton)
