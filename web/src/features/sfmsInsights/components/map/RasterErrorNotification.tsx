import React from 'react'
import { Alert, AlertColor, Snackbar } from '@mui/material'
import { RasterError } from './layerManager'

interface RasterErrorNotificationProps {
  error: RasterError | null
  onClose: () => void
  rasterLabel?: string
}

const getAlertSeverity = (errorType: RasterError['type']): AlertColor => {
  switch (errorType) {
    case 'not_found':
      return 'warning'
    case 'forbidden':
      return 'error'
    case 'network':
    case 'unknown':
    default:
      return 'warning'
  }
}

const getErrorMessage = (error: RasterError, rasterLabel: string): string => {
  switch (error.type) {
    case 'not_found':
      return `${rasterLabel} data not available for this date. It may not be generated yet.`
    case 'forbidden':
      return `Access denied to ${rasterLabel} data. Please check your authentication.`
    case 'network':
      return `${rasterLabel} data not available. It may not exist for this date or there was a network issue.`
    case 'unknown':
    default:
      return error.message || `Failed to load ${rasterLabel} data.`
  }
}

const RasterErrorNotification = ({ error, onClose, rasterLabel = 'Raster' }: RasterErrorNotificationProps) => {
  if (!error) {
    return null
  }

  const severity = getAlertSeverity(error.type)
  const message = getErrorMessage(error, rasterLabel)

  return (
    <Snackbar
      anchorOrigin={{ horizontal: 'center', vertical: 'bottom' }}
      autoHideDuration={6000}
      onClose={onClose}
      open={true}
    >
      <Alert onClose={onClose} severity={severity} variant="filled">
        {message}
      </Alert>
    </Snackbar>
  )
}

export default React.memo(RasterErrorNotification)
