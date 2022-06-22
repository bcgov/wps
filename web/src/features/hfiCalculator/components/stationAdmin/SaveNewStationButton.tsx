import React from 'react'
import { Button } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'

export interface SaveNewStationButtonProps {
  testId?: string
  invalidNewStation: boolean
  handleSave: () => void
}

const useStyles = makeStyles(() => ({
  actionButton: {
    minWidth: 100,
    margin: theme.spacing(1),
    float: 'right'
  }
}))

const SaveNewStationButton = ({ invalidNewStation, handleSave }: SaveNewStationButtonProps) => {
  const classes = useStyles()

  return (
    <Button
      variant="contained"
      color="primary"
      disabled={invalidNewStation}
      className={classes.actionButton}
      onClick={handleSave}
      data-testid={'save-new-station-button'}
    >
      Save
    </Button>
  )
}

export default React.memo(SaveNewStationButton)
