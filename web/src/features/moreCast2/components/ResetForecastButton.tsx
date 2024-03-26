import React from 'react'
import { Button, Dialog, DialogActions, DialogContent, DialogContentText } from '@mui/material'

export interface ResetForecastButtonProps {
  className?: string
  enabled: boolean
  label: string
  showResetDialog: boolean
  setShowResetDialog: React.Dispatch<React.SetStateAction<boolean>>
  handleResetButtonConfirm: () => void
  onClick: () => void
}

const ResetForecastButton = ({
  className,
  enabled,
  label,
  showResetDialog,
  setShowResetDialog,
  handleResetButtonConfirm,
  onClick
}: ResetForecastButtonProps) => {
  const handleResetDialogClose = () => {
    setShowResetDialog(false)
  }
  return (
    <>
      <Button
        className={className}
        variant="contained"
        data-testid={'reset-forecast-button'}
        disabled={!enabled}
        onClick={onClick}
      >
        {label}
      </Button>
      <Dialog open={showResetDialog} data-testid={'reset-dialog'}>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete your unsaved forecasts? This will reset all forecasts that have not been
            published to WF1.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleResetDialogClose}>Cancel</Button>
          <Button onClick={handleResetButtonConfirm} data-testid={'reset-forecast-confirm-button'}>
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default React.memo(ResetForecastButton)
