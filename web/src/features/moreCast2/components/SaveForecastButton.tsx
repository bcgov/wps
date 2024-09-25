import React from 'react'
import SaveIcon from '@mui/icons-material/Save'
import { Button } from '@mui/material'
import { useSelector } from 'react-redux'
import { selectMorecastInputValid } from '@/features/moreCast2/slices/validInputSlice'

export interface SubmitForecastButtonProps {
  className?: string
  enabled: boolean
  label: string
  onClick: () => void
}

const SaveForecastButton = ({ className, enabled, label, onClick }: SubmitForecastButtonProps) => {
  const isValid = useSelector(selectMorecastInputValid)

  return (
    <Button
      className={className}
      variant="contained"
      data-testid={'submit-forecast-button'}
      disabled={!enabled || !isValid}
      onClick={onClick}
      startIcon={<SaveIcon />}
    >
      {label}
    </Button>
  )
}

export default React.memo(SaveForecastButton)
