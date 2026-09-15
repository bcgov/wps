import { Alert, type AlertColor, Snackbar } from '@mui/material'
import type { SnackbarProps } from '@mui/material/Snackbar'
import type { ReactNode } from 'react'

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
  const handleSnackbarClose: NonNullable<SnackbarProps['onClose']> = (_event, reason) => {
    if (reason !== 'clickaway') onClose()
  }

  return (
    <Snackbar
      data-testid={testId}
      open={open}
      autoHideDuration={autoHideDuration}
      onClose={handleSnackbarClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'left' }}
      sx={theme => ({
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        transform: 'none',
        width: '100%',
        maxWidth: 'none',
        [`${theme.breakpoints.down('lg')} and (orientation: landscape)`]: {
          top: 'env(safe-area-inset-top)'
        },
        '& .MuiAlert-root': {
          width: '100%',
          borderRadius: 0
        }
      })}
    >
      <Alert icon={icon} onClose={onClose} severity={severity} variant="filled">
        {message}
      </Alert>
    </Snackbar>
  )
}

export default NotificationSnackbar
