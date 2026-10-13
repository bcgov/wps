import { Alert, type AlertColor, Box } from '@mui/material'
import { type ReactNode, useEffect } from 'react'

interface NotificationSnackbarProps {
  open: boolean
  onClose: () => void
  message: string
  severity?: AlertColor
  autoHideDuration?: number | null
  icon?: ReactNode
  testId?: string
}

const NotificationSnackbar = ({
  open,
  onClose,
  message,
  severity = 'error',
  autoHideDuration = 6000,
  icon,
  testId
}: NotificationSnackbarProps) => {
  useEffect(() => {
    if (!open || autoHideDuration === null) return

    const timeout = window.setTimeout(onClose, autoHideDuration)
    return () => window.clearTimeout(timeout)
  }, [autoHideDuration, onClose, open])

  if (!open) return null

  return (
    <Box
      data-testid={testId}
      sx={theme => ({
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        zIndex: theme.zIndex.snackbar,
        [`${theme.breakpoints.down('lg')} and (orientation: landscape)`]: {
          top: 'env(safe-area-inset-top)'
        }
      })}
    >
      <Alert
        icon={icon}
        onClose={onClose}
        severity={severity}
        variant="filled"
        sx={{ borderRadius: 0, boxSizing: 'border-box', width: '100%' }}
      >
        {message}
      </Alert>
    </Box>
  )
}

export default NotificationSnackbar
