import { FormControl, FormControlLabel, FormLabel, Radio, RadioGroup } from '@mui/material'
import React from 'react'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { isNull } from 'lodash'
import { theme } from 'app/theme'

export interface ActualForecastControlProps {
  runType: RunType
  setRunType: React.Dispatch<React.SetStateAction<RunType>>
}
const ActualForecastControl = ({ runType, setRunType }: ActualForecastControlProps) => {
  const changeHandler = (_: React.ChangeEvent<{}>, value: string | null) => {
    if (!isNull(value)) {
      setRunType(value as RunType)
    }
  }
  return (
    <FormControl
      variant="outlined"
      sx={{
        border: '1px solid rgba(0, 0, 0, 0.23)',
        borderRadius: '4px',
        padding: '8px 12px 4px',
        position: 'relative',
        margin: theme.spacing(1)
      }}
    >
      <FormLabel
        sx={{
          fontSize: '0.75rem',
          color: 'rgba(0, 0, 0, 0.6)',
          position: 'absolute',
          top: '-10px',
          left: '12px',
          backgroundColor: 'white',
          padding: '0 4px'
        }}
      >
        Time Frame
      </FormLabel>
      <RadioGroup row value={runType} onChange={changeHandler}>
        <FormControlLabel
          value={RunType.ACTUAL}
          control={
            <Radio inputProps={{ 'data-testid': 'actual-radio' } as React.InputHTMLAttributes<HTMLInputElement>} />
          }
          label="Actual"
        />
        <FormControlLabel
          value={RunType.FORECAST}
          control={
            <Radio inputProps={{ 'data-testid': 'forecast-radio' } as React.InputHTMLAttributes<HTMLInputElement>} />
          }
          label="Forecast"
        />
      </RadioGroup>
    </FormControl>
  )
}

export default React.memo(ActualForecastControl)
