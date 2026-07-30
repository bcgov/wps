import { Close as CloseIcon } from '@mui/icons-material'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Typography,
  useMediaQuery
} from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { sendFeedback } from '@sentry/react'
import { type SyntheticEvent, useEffect, useRef, useState } from 'react'
import NotificationSnackbar from '@/components/NotificationSnackbar'

interface FeedbackDialogProps {
  defaultEmail?: string
  isOnline: boolean
  onClose: () => void
  open: boolean
}

const inputSx = {
  '& .MuiInputBase-input': {
    fontSize: '1rem'
  }
}

const floatedLabelSlotProps = { inputLabel: { shrink: true } }

export const FeedbackDialog = ({ defaultEmail, isOnline, onClose, open }: FeedbackDialogProps) => {
  const theme = useTheme()
  const isFullScreen = useMediaQuery(theme.breakpoints.down('lg'))
  const submissionId = useRef(0)
  const [name, setName] = useState('')
  const [email, setEmail] = useState(defaultEmail ?? '')
  const [message, setMessage] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)

  useEffect(() => {
    if (open) {
      setName('')
      setEmail(defaultEmail ?? '')
      setMessage('')
      setError(null)
      setIsSubmitting(false)
    }
  }, [defaultEmail, open])

  const handleClose = () => {
    submissionId.current += 1
    setIsSubmitting(false)
    setError(null)
    onClose()
  }

  const handleSubmit = async (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!isOnline) {
      return
    }
    const trimmedMessage = message.trim()
    if (!trimmedMessage) {
      setError('Please enter a description.')
      return
    }

    const currentSubmissionId = ++submissionId.current
    setError(null)
    setIsSubmitting(true)

    try {
      await sendFeedback(
        {
          message: trimmedMessage,
          name: name.trim() || undefined,
          email: email.trim() || undefined
        },
        { includeReplay: true }
      )
      if (submissionId.current !== currentSubmissionId) {
        return
      }
      setIsSubmitting(false)
      setShowSuccess(true)
      onClose()
    } catch {
      if (submissionId.current !== currentSubmissionId) {
        return
      }
      setIsSubmitting(false)
      setError("We couldn't send your feedback. Please check your connection and try again.")
    }
  }

  return (
    <>
      <Dialog
        aria-labelledby="feedback-dialog-title"
        fullScreen={isFullScreen}
        fullWidth
        maxWidth="sm"
        onClose={handleClose}
        open={open}
        slotProps={{
          paper: {
            sx: isFullScreen
              ? {
                  height: '100dvh',
                  maxHeight: '100dvh'
                }
              : {
                  maxHeight: 'calc(100dvh - 32px)'
                }
          }
        }}
      >
        <DialogTitle
          id="feedback-dialog-title"
          sx={{
            alignItems: 'center',
            display: 'flex',
            flexShrink: 0,
            justifyContent: 'space-between',
            paddingTop: 'calc(16px + env(safe-area-inset-top))'
          }}
        >
          <Typography component="span" variant="h6">
            Submit Feedback
          </Typography>
          <IconButton aria-label="close feedback" edge="end" onClick={handleClose}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{ display: 'flex', flex: 1, flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}
        >
          <DialogContent dividers sx={{ minHeight: 0, overflowY: 'auto', overscrollBehavior: 'contain' }}>
            {!isOnline && (
              <Alert severity="warning" sx={{ marginBottom: 2 }}>
                Feedback is unavailable while offline.
              </Alert>
            )}
            {error && (
              <Alert severity="error" sx={{ marginBottom: 2 }}>
                {error}
              </Alert>
            )}
            <TextField
              autoComplete="name"
              disabled={!isOnline || isSubmitting}
              fullWidth
              label="Name"
              margin="normal"
              onChange={event => setName(event.target.value)}
              slotProps={floatedLabelSlotProps}
              sx={inputSx}
              value={name}
            />
            <TextField
              autoComplete="email"
              disabled={!isOnline || isSubmitting}
              fullWidth
              label="Email"
              margin="normal"
              onChange={event => setEmail(event.target.value)}
              sx={inputSx}
              type="email"
              value={email}
            />
            <TextField
              disabled={!isOnline || isSubmitting}
              fullWidth
              label="Description"
              margin="normal"
              minRows={5}
              multiline
              onChange={event => setMessage(event.target.value)}
              required
              slotProps={floatedLabelSlotProps}
              sx={inputSx}
              value={message}
            />
          </DialogContent>
          <DialogActions
            sx={{
              backgroundColor: 'background.paper',
              flexShrink: 0,
              padding: 2,
              paddingBottom: 'calc(16px + env(safe-area-inset-bottom))'
            }}
          >
            <Button onClick={handleClose}>Cancel</Button>
            <Button disabled={!isOnline || isSubmitting} type="submit" variant="contained">
              {isSubmitting && <CircularProgress aria-hidden size={18} sx={{ marginRight: 1 }} />}
              {isSubmitting ? 'Sending…' : 'Send Feedback'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
      <NotificationSnackbar
        autoHideDuration={4000}
        message="Thank you for your feedback."
        onClose={() => setShowSuccess(false)}
        open={showSuccess}
        severity="success"
      />
    </>
  )
}
