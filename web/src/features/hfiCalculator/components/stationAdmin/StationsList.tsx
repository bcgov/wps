import React from 'react'
import { Box, Autocomplete, TextField, Grid, Typography, Tooltip } from '@mui/material'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { AdminStation } from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import makeStyles from '@mui/styles/makeStyles'

export interface AddStationsList {
  testId?: string
  newStations: AdminStation[]
}

const useStyles = makeStyles({
  autocomplete: {
    minWidth: 300
  },
  tooltip: {
    maxHeight: '0.8em'
  }
})

export const AddStationsList = ({ newStations }: AddStationsList): JSX.Element => {
  const classes = useStyles()

  return (
    <Box sx={{ marginTop: 5 }}>
      <Grid container justifyContent="center" spacing={1}>
        {newStations.map((newStation, index) => (
          <Grid item key={index}>
            <Grid container direction="row" key={index} spacing={1}>
              <Grid item key={index}>
                {index === 0 && (
                  <Typography>
                    <strong>Planning Area</strong>
                  </Typography>
                )}
                <Autocomplete
                  className={classes.autocomplete}
                  key={index}
                  renderInput={params => (
                    <TextField
                      {...params}
                      label="Select Planning Area"
                      variant="outlined"
                    />
                  )}
                  options={[]}
                />
              </Grid>
              <Grid item key={index}>
                {index === 0 && (
                  <Typography>
                    <strong>Station</strong>
                  </Typography>
                )}

                <Autocomplete
                  className={classes.autocomplete}
                  key={index}
                  renderInput={params => (
                    <TextField {...params} label="Select Station" variant="outlined" />
                  )}
                  options={[]}
                />
              </Grid>
              <Grid item key={index}>
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
                  key={index}
                  renderInput={params => (
                    <TextField {...params} label="Select Fuel Type" variant="outlined" />
                  )}
                  options={[]}
                />
              </Grid>
            </Grid>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default React.memo(AddStationsList)
