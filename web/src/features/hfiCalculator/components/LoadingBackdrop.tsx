import { Backdrop, CircularProgress } from '@mui/material'
import React from 'react'

export interface LoadingBackdropProps {
  isLoadingWithoutError: boolean
}

const LoadingBackdrop = ({ isLoadingWithoutError }: LoadingBackdropProps) => {
  return (
    <Backdrop
      data-testid="loading-backdrop"
      sx={{ zIndex: theme => theme.zIndex.drawer + 101 }}
      open={isLoadingWithoutError}
    >
      <CircularProgress />
    </Backdrop>
  )
}

export default React.memo(LoadingBackdrop)
