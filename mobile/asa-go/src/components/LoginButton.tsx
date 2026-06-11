import { Button, Typography, useTheme } from '@mui/material'
import { useDispatch } from 'react-redux'
import { authenticate } from '@/slices/authenticationSlice'
import type { AppDispatch } from '@/store'

const LoginButton = () => {
  const dispatch: AppDispatch = useDispatch()
  const theme = useTheme()

  const handleLogin = () => {
    dispatch(authenticate())
  }
  return (
    <Button
      onClick={handleLogin}
      size="large"
      sx={{
        bgcolor: theme.palette.secondary.main,
        color: theme.palette.primary.main,
        display: 'block',
        minWidth: '100px'
      }}
      variant="contained"
    >
      <Typography
        sx={{
          justifyContent: 'center',
          display: 'flex',
          fontWeight: 'bold'
        }}
      >
        IDIR
      </Typography>
    </Button>
  )
}

export default LoginButton
