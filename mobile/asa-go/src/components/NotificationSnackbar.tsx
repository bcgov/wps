import { Alert, type AlertColor, Snackbar } from '@mui/material'
import type { SnackbarOrigin } from '@mui/material/Snackbar'

interface NotificationSnackbarProps {
  open: boolean
  onClose: () => void
  message: string
  anchorOrigin?: SnackbarOrigin
  severity?: AlertColor
  autoHideDuration?: number | null
}

const NotificationSnackbar = ({
  open,
  onClose,
  message,
  anchorOrigin = { vertical: 'top', horizontal: 'center' },
  severity = 'error',
  autoHideDuration = 6000
}: NotificationSnackbarProps) => (
  <Snackbar
    open={open}
    autoHideDuration={autoHideDuration}
    onClose={onClose}
    anchorOrigin={anchorOrigin}
    sx={{
      ...(anchorOrigin.vertical === 'top'
        ? {
            top: {
              xs: 'calc(env(safe-area-inset-top) + 8px)',
              sm: 'calc(env(safe-area-inset-top) + 24px)'
            }
          }
        : {}),
      width: {
        xs: 'calc(100% - 16px)',
        sm: 'min(420px, calc(100% - 48px))'
      },
      maxWidth: '100%'
    }}
  >
    <Alert onClose={onClose} severity={severity} variant="filled">
      {message}
    </Alert>
  </Snackbar>
)

export default NotificationSnackbar
