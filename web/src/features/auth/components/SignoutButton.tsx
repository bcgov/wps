import React from 'react'
import { Button } from '@mui/material'
import { createTheme, ThemeProvider } from '@mui/material/styles'
import { signout } from 'features/auth/slices/authenticationSlice'
import { useDispatch, useSelector } from 'react-redux'
import { selectAuthentication } from 'app/rootReducer'
import { AppDispatch } from 'app/store'

const SignoutButton = () => {
  const { idToken } = useSelector(selectAuthentication)

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
              dispatch(signout(idToken))
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
