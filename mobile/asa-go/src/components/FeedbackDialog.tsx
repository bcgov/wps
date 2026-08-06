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
import { type SyntheticEvent, useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import NotificationSnackbar from '@/components/NotificationSnackbar'
import { resetFeedbackSubmission, setFeedbackError, submitFeedback } from '@/slices/feedbackSlice'
import { type AppDispatch, selectFeedback } from '@/store'

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
  const dispatch: AppDispatch = useDispatch()
  const { error, isSubmitting, submitted } = useSelector(selectFeedback)
  const [name, setName] = useState('')
  const [email, setEmail] = useState(defaultEmail ?? '')
  const [message, setMessage] = useState('')
  const [showSuccess, setShowSuccess] = useState(false)

  useEffect(() => {
    if (open) {
      setName('')
      setEmail(defaultEmail ?? '')
      setMessage('')
      dispatch(resetFeedbackSubmission())
    }
  }, [defaultEmail, dispatch, open])

  useEffect(() => {
    if (!submitted) {
      return
    }
    setShowSuccess(true)
    dispatch(resetFeedbackSubmission())
    onClose()
  }, [dispatch, onClose, submitted])

  const handleClose = () => {
    dispatch(resetFeedbackSubmission())
    onClose()
  }

  const handleSubmit = (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!isOnline) {
      return
    }
    const trimmedMessage = message.trim()
    if (!trimmedMessage) {
      dispatch(setFeedbackError('Please enter a description.'))
      return
    }

    dispatch(
      submitFeedback({
        message: trimmedMessage,
        name: name.trim() || undefined,
        email: email.trim() || undefined
      })
    )
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
