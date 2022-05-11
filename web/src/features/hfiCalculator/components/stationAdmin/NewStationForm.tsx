import React, { Dispatch, SetStateAction } from 'react'
import { Box, Autocomplete, TextField, Grid, Typography, Tooltip } from '@mui/material'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import {
  AddStationOptions,
  AdminStation
} from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import makeStyles from '@mui/styles/makeStyles'
import { isNull, isUndefined } from 'lodash'

export interface NewStationFormProps {
  testId?: string
  addStationOptions?: AddStationOptions
  newStation: AdminStation
  setNewStation: Dispatch<SetStateAction<AdminStation>>
  invalid: boolean
  setInvalid: Dispatch<SetStateAction<boolean>>
  handleFormChange: () => void
  stationAddedError: string | null
}

const useStyles = makeStyles({
  autocomplete: {
    minWidth: 300
  },
  tooltip: {
    maxHeight: '0.75em'
  },
  toolTipText: {
    fontSize: 14
  }
})

export const NewStationForm = ({
  addStationOptions,
  newStation,
  setNewStation,
  invalid,
  setInvalid,
  handleFormChange,
  stationAddedError
}: NewStationFormProps): JSX.Element => {
  const classes = useStyles()

  const invalidNewStation = (station: AdminStation) => {
    const missingFields =
      isUndefined(station.planningArea) ||
      isUndefined(station.station) ||
      isUndefined(station.fuelType)
    setInvalid(missingFields && station.dirty)
  }

  const planningAreaError =
    (newStation.dirty && isUndefined(newStation.planningArea)) ||
    !isNull(stationAddedError)

  const stationError =
    (newStation.dirty && isUndefined(newStation.station)) || !isNull(stationAddedError)

  const fuelTypeError =
    (newStation.dirty && isUndefined(newStation.fuelType)) || !isNull(stationAddedError)

  const toolTipText = (
    <div className={classes.toolTipText}>Grass curing is set in WFWX</div>
  )

  return (
    <Box sx={{ marginTop: 5 }}>
      <Grid container justifyContent="center" spacing={1}>
        <Grid item>
          <Grid container direction="row" spacing={1}>
            <Grid item>
              <Typography>
                <strong>Planning Area</strong>
              </Typography>
              <Autocomplete
                className={classes.autocomplete}
                data-testid={'select-planning-area'}
                options={addStationOptions ? addStationOptions.planning_areas : []}
                getOptionLabel={option => option?.name}
                renderInput={params => (
                  <TextField
                    {...params}
                    label="Select Planning Area"
                    variant="outlined"
                    error={planningAreaError}
                  />
                )}
                onChange={(_, value) => {
                  const changedNewStation = {
                    ...newStation,
                    dirty: true,
                    planningArea: isNull(value) ? undefined : value
                  }
                  setNewStation(changedNewStation)
                  invalidNewStation(changedNewStation)
                  handleFormChange()
                }}
              />
            </Grid>
            <Grid item>
              <Typography>
                <strong>Station</strong>
              </Typography>

              <Autocomplete
                className={classes.autocomplete}
                data-testid={'select-station'}
                options={addStationOptions ? addStationOptions.stations : []}
                getOptionLabel={option => option?.name}
                renderInput={params => (
                  <TextField
                    {...params}
                    label="Select Station"
                    variant="outlined"
                    error={stationError}
                  />
                )}
                onChange={(_, value) => {
                  const changedNewStation = {
                    ...newStation,
                    dirty: true,
                    station: isNull(value) ? undefined : value
                  }
                  setNewStation(changedNewStation)
                  invalidNewStation(changedNewStation)
                  handleFormChange()
                }}
              />
            </Grid>
            <Grid item>
              <Typography>
                <strong>Fuel Type</strong>
                <Tooltip
                  className={classes.tooltip}
                  title={toolTipText}
                  aria-label="grass-curing-is-set-in-wfwx"
                >
                  <InfoOutlinedIcon></InfoOutlinedIcon>
                </Tooltip>
              </Typography>
              <Autocomplete
                data-testid={'select-fuel-type'}
                className={classes.autocomplete}
                options={addStationOptions ? addStationOptions.fuel_types : []}
                getOptionLabel={option => option?.abbrev}
                renderInput={params => (
                  <TextField
                    {...params}
                    label="Select Fuel Type"
                    variant="outlined"
                    error={fuelTypeError}
                  />
                )}
                onChange={(_, value) => {
                  const changedNewStation = {
                    ...newStation,
                    dirty: true,
                    fuelType: isNull(value) ? undefined : value
                  }
                  setNewStation(changedNewStation)
                  invalidNewStation(changedNewStation)
                }}
              />
            </Grid>
          </Grid>
        </Grid>
        {invalid && (
          <Grid
            container
            direction="row"
            justifyContent="center"
            spacing={1}
            marginTop={5}
          >
            <Grid item>
              <ErrorOutlineIcon color="error" />
            </Grid>
            <Grid item>
              <Typography variant="body1">
                Please complete empty fields to continue
              </Typography>
            </Grid>
          </Grid>
        )}
        {!isNull(stationAddedError) && (
          <Grid
            container
            direction="row"
            justifyContent="center"
            spacing={1}
            marginTop={5}
          >
            <Grid item>
              <ErrorOutlineIcon color="error" />
            </Grid>
            <Grid item>
              <Typography variant="body1">Station already exists</Typography>
            </Grid>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}

export default React.memo(NewStationForm)
