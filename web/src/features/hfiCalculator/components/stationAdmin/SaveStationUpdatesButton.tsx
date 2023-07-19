import React from 'react'
import { styled } from '@mui/material/styles'
import { Button } from '@mui/material'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import { theme } from 'app/theme'
import { isEmpty, isUndefined, some } from 'lodash'

const PREFIX = 'SaveStationUpdatesButton'

const classes = {
  actionButton: `${PREFIX}-actionButton`
}

const StyledButton = styled(Button)(() => ({
  [`&.${classes.actionButton}`]: {
    minWidth: 100,
    margin: theme.spacing(1),
    float: 'right'
  }
}))

export interface SaveStationUpdatesButtonProps {
  testId?: string
  addedStations: StationAdminRow[]
  removedStations: StationAdminRow[]
  handleSave: () => void
}

const SaveStationUpdatesButton = ({ addedStations, removedStations, handleSave }: SaveStationUpdatesButtonProps) => {
  return (
    <StyledButton
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
    </StyledButton>
  )
}

export default React.memo(SaveStationUpdatesButton)
