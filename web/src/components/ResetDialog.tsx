import React from 'react'
import { Button, Dialog, DialogActions, DialogContent, DialogContentText } from '@mui/material'
import { theme } from "app/theme"

export interface ResetDialogProps {
  showResetDialog: boolean
  setShowResetDialog: React.Dispatch<React.SetStateAction<boolean>>
  handleResetButtonConfirm: () => void
  message: string
}

const ResetDialog = ({
  showResetDialog,
  setShowResetDialog,
  handleResetButtonConfirm,
  message
}: ResetDialogProps) => {
  const handleResetDialogClose = () => {
    setShowResetDialog(false)
  }
  return (
    <>
      <Dialog
        open={showResetDialog}
        onClose={(handleResetDialogClose)}
        data-testid={'reset-dialog'}
        PaperProps={{ sx: { border: 2, borderColor: '#808080' } }}
      >
        <DialogContent>
          <DialogContentText>
              {message}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" onClick={handleResetDialogClose} data-testid={'reset-dialog-cancel-button'}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleResetButtonConfirm}
            data-testid={'reset-dialog-confirm-button'}
            sx={{
              border: `1px solid ${theme.palette.primary.main}`,
              bgcolor: 'error.main',
              color: 'error.contrastText',
              '&:hover': { bgcolor: 'error.dark'}}}
          >
            Reset
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default React.memo(ResetDialog)
