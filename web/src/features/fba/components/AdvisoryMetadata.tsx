import { Autocomplete, Box, Grid, TextField, Typography } from '@mui/material'
import React from 'react'
import { DateTime } from 'luxon'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { isNull } from 'lodash'

export interface AdvisoryMetadataProps {
  testId?: string
  runType: string
  setRunType: React.Dispatch<React.SetStateAction<RunType>>
  forDate: DateTime
  issueDate: DateTime | null
  setIssueDate: React.Dispatch<React.SetStateAction<DateTime | null>>
}
const AdvisoryMetadata = ({ runType, setRunType, forDate, issueDate }: AdvisoryMetadataProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isNull(value)) {
      setRunType(value)
    }
  }
  return (
    <Box sx={{ width: 270 }}>
      <Grid container spacing={2}>
        <Grid item xs>
          <Autocomplete
            disablePortal
            disableClearable
            autoComplete
            size="small"
            id="asa-forecast-actual-select"
            options={[RunType.FORECAST, RunType.ACTUAL]}
            defaultValue={runType}
            onChange={changeHandler}
            renderInput={params => <TextField {...params} label="Forecast or Actual" />}
          />{' '}
          <Typography variant="subtitle2">is for {forDate.toISODate()}</Typography>
          <Typography variant="subtitle2">issued on {!isNull(issueDate) ? issueDate.toISO() : ''}</Typography>
        </Grid>
      </Grid>
    </Box>
  )
}

export default React.memo(AdvisoryMetadata)
