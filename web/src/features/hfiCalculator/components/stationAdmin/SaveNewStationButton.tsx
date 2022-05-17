import React from 'react'
import { Button } from '@mui/material'
import { AdminStation } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'
import { isEmpty, values } from 'lodash'

export interface SaveNewStationButtonProps {
  testId?: string
  newStation: AdminStation
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

const SaveNewStationButton = ({ newStation, invalidNewStation, handleSave }: SaveNewStationButtonProps) => {
  const classes = useStyles()

  return (
    <Button
      variant="contained"
      color="primary"
      disabled={invalidNewStation || values(newStation).every(isEmpty)}
      className={classes.actionButton}
      onClick={handleSave}
      data-testid={'save-new-station-button'}
    >
      Save
    </Button>
  )
}

export default React.memo(SaveNewStationButton)
