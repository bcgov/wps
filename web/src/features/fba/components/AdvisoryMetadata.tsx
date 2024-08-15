import { Autocomplete, TextField } from '@mui/material'
import React from 'react'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { isNull } from 'lodash'

export interface AdvisoryMetadataProps {
  testId?: string
  runType: string
  setRunType: React.Dispatch<React.SetStateAction<RunType>>
}
const AdvisoryMetadata = ({ runType, setRunType }: AdvisoryMetadataProps) => {
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isNull(value)) {
      setRunType(value)
    }
  }
  return (
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
    />
  )
}

export default React.memo(AdvisoryMetadata)
