import React from 'react'
import { Button } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { theme } from 'app/theme'
import { isEmpty, isUndefined, some } from 'lodash'

export interface SaveStationUpdatesButtonProps {
  testId?: string
  addedStations: StationAdminRow[]
  removedStations: StationAdminRow[]
  handleSave: () => void
}

const useStyles = makeStyles(() => ({
  actionButton: {
    minWidth: 100,
    margin: theme.spacing(1),
    float: 'right'
  }
}))

const SaveStationUpdatesButton = ({ addedStations, removedStations, handleSave }: SaveStationUpdatesButtonProps) => {
  const classes = useStyles()

  return (
    <Button
      variant="contained"
      color="primary"
      disabled={
        (isEmpty(addedStations) && isEmpty(removedStations)) ||
        some(addedStations, addedStation => isUndefined(addedStation.fuelType) || isUndefined(addedStation.station))
      }
      className={classes.actionButton}
      onClick={handleSave}
      data-testid={'save-new-station-button'}
    >
      Save
    </Button>
  )
}

export default React.memo(SaveStationUpdatesButton)
