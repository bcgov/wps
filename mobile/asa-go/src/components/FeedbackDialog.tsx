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
  Snackbar,
  TextField,
  Typography,
  useMediaQuery
} from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { sendFeedback } from '@sentry/react'
import { type FormEvent, useEffect, useRef, useState } from 'react'

interface FeedbackDialogProps {
  defaultEmail?: string
  onClose: () => void
  open: boolean
}

const inputSx = {
  '& .MuiInputBase-input': {
    fontSize: '1rem'
  }
}

export const FeedbackDialog = ({ defaultEmail, onClose, open }: FeedbackDialogProps) => {
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

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
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
            {error && (
              <Alert severity="error" sx={{ marginBottom: 2 }}>
                {error}
              </Alert>
            )}
            <TextField
              autoComplete="name"
              fullWidth
              label="Name"
              margin="normal"
              onChange={event => setName(event.target.value)}
              sx={inputSx}
              value={name}
            />
            <TextField
              autoComplete="email"
              fullWidth
              label="Email"
              margin="normal"
              onChange={event => setEmail(event.target.value)}
              sx={inputSx}
              type="email"
              value={email}
            />
            <TextField
              fullWidth
              label="Description"
              margin="normal"
              minRows={5}
              multiline
              onChange={event => setMessage(event.target.value)}
              required
              slotProps={{ inputLabel: { shrink: true } }}
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
            <Button disabled={isSubmitting} type="submit" variant="contained">
              {isSubmitting && <CircularProgress aria-hidden size={18} sx={{ marginRight: 1 }} />}
              {isSubmitting ? 'Sending…' : 'Send Feedback'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
      <Snackbar
        anchorOrigin={{ horizontal: 'center', vertical: 'top' }}
        autoHideDuration={4000}
        onClose={() => setShowSuccess(false)}
        open={showSuccess}
      >
        <Alert onClose={() => setShowSuccess(false)} severity="success" variant="filled">
          Thank you for your feedback.
        </Alert>
      </Snackbar>
    </>
  )
}
