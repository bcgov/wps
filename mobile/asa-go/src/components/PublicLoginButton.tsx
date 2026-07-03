import { Button } from '@mui/material'
import { useDispatch } from 'react-redux'
import { continueAsGuestSession } from '@/slices/authenticationSlice'
import type { AppDispatch } from '@/store'

const PublicLoginButton = () => {
  const dispatch: AppDispatch = useDispatch()
  const handleClick = () => {
    dispatch(continueAsGuestSession())
  }
  return (
    <Button onClick={handleClick} sx={{ color: 'white', textDecoration: 'underline' }}>
      Continue as guest
    </Button>
  )
}

export default PublicLoginButton
