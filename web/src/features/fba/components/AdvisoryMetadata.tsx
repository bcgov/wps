import { Autocomplete, Box, Grid, TextField, Typography } from '@mui/material'
import React from 'react'
import { DateTime } from 'luxon'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

export interface AdvisoryMetadataProps {
  testId?: string
  runType: string
  setRunType: React.Dispatch<React.SetStateAction<RunType>>
  forDate: DateTime
  runDate: DateTime
  setRunDate: React.Dispatch<React.SetStateAction<DateTime>>
}
const AdvisoryMetadata = ({ runType: run_type, forDate: for_date, runDate: run_date }: AdvisoryMetadataProps) => {
  return (
    <Box sx={{ width: 270 }}>
      <Grid container spacing={2}>
        <Grid item xs>
          <Autocomplete
            disablePortal
            autoComplete
            size="small"
            id="asa-forecast-actual-select"
            options={[RunType.FORECAST, RunType.ACTUAL]}
            defaultValue={run_type}
            renderInput={params => <TextField {...params} label="Forecast or Actual" />}
          />{' '}
          <Typography variant="subtitle2">
            is for {for_date.toISODate()} issued on {run_date.toISODate()}
          </Typography>
        </Grid>
      </Grid>
    </Box>
  )
}

export default React.memo(AdvisoryMetadata)
