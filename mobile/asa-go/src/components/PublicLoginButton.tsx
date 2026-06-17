import { Button } from '@mui/material'
import { useDispatch } from 'react-redux'
import { continueAsGuest } from '@/slices/authenticationSlice'
import type { AppDispatch } from '@/store'

const PublicLoginButton = () => {
  const dispatch: AppDispatch = useDispatch()
  const handleClick = () => {
    dispatch(continueAsGuest())
  }
  return (
    <Button onClick={handleClick} sx={{ color: 'white', textDecoration: 'underline' }}>
      Continue as guest
    </Button>
  )
}

export default PublicLoginButton
