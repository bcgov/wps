import React from 'react'
import { Box, Autocomplete, TextField, Grid, Typography, Tooltip } from '@mui/material'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import { AdminStation } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import makeStyles from '@mui/styles/makeStyles'
import { isUndefined } from 'lodash'

export interface StationListProps {
  testId?: string
  newStations: AdminStation[]
  someStationsEmpty: boolean
}

const useStyles = makeStyles({
  autocomplete: {
    minWidth: 300
  },
  tooltip: {
    maxHeight: '0.8em'
  }
})

export const StationList = ({
  newStations,
  someStationsEmpty
}: StationListProps): JSX.Element => {
  const classes = useStyles()

  return (
    <Box sx={{ marginTop: 5 }}>
      <Grid container justifyContent="center" spacing={1}>
        {newStations.map((newStation, index) => (
          <Grid item key={`add-station-row-${index}`}>
            <Grid
              container
              direction="row"
              key={`add-station-row-container-${index}`}
              spacing={1}
            >
              <Grid item key={`planning-area-${index}`}>
                {index === 0 && (
                  <Typography>
                    <strong>Planning Area</strong>
                  </Typography>
                )}
                <Autocomplete
                  className={classes.autocomplete}
                  value={newStation.planningArea?.name}
                  key={`autocomplete-planning-area-${index}`}
                  renderInput={params => (
                    <TextField
                      {...params}
                      label="Select Planning Area"
                      variant="outlined"
                      error={newStation.dirty && isUndefined(newStation.planningArea)}
                    />
                  )}
                  options={[]}
                />
              </Grid>
              <Grid item key={`station-${index}`}>
                {index === 0 && (
                  <Typography>
                    <strong>Station</strong>
                  </Typography>
                )}

                <Autocomplete
                  className={classes.autocomplete}
                  key={`autocomplete-station-type-${index}`}
                  renderInput={params => (
                    <TextField
                      {...params}
                      label="Select Station"
                      variant="outlined"
                      error={newStation.dirty && isUndefined(newStation.station)}
                    />
                  )}
                  options={[]}
                />
              </Grid>
              <Grid item key={`fuel-type-${index}`}>
                {index === 0 && (
                  <Typography>
                    <strong>Fuel Type</strong>
                    <Tooltip
                      className={classes.tooltip}
                      title="Grass curing is set in WFWX"
                      aria-label="grass-curing-is-set-in-wfwx"
                    >
                      <InfoOutlinedIcon></InfoOutlinedIcon>
                    </Tooltip>
                  </Typography>
                )}

                <Autocomplete
                  className={classes.autocomplete}
                  key={`autocomplete-fuel-type-${index}`}
                  renderInput={params => (
                    <TextField
                      {...params}
                      label="Select Fuel Type"
                      variant="outlined"
                      error={newStation.dirty && isUndefined(newStation.fuelType)}
                    />
                  )}
                  options={[]}
                />
              </Grid>
            </Grid>
          </Grid>
        ))}
        {someStationsEmpty && (
          <Grid
            container
            direction="row"
            justifyContent="center"
            spacing={1}
            marginTop={5}
          >
            <Grid item spacing={1}>
              <ErrorOutlineIcon color="error" />
            </Grid>
            <Grid item spacing={1}>
              <Typography variant="body1">
                Please complete empty fields to continue
              </Typography>
            </Grid>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}

export default React.memo(StationList)
