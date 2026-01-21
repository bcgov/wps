import React from 'react'
import { styled } from '@mui/material/styles'
import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  ToggleButton,
  ToggleButtonGroup,
  TextField,
  Button,
  Box
} from '@mui/material'

import {
  AggregationPeriod,
  ReferencePeriod,
  STANDARD_REFERENCE_PERIODS,
  WeatherVariable,
  WEATHER_VARIABLE_LABELS
} from '../interfaces'

const PREFIX = 'ClimatologyControls'

const classes = {
  root: `${PREFIX}-root`,
  formControl: `${PREFIX}-formControl`,
  row: `${PREFIX}-row`,
  yearInputs: `${PREFIX}-yearInputs`,
  yearField: `${PREFIX}-yearField`,
  buttons: `${PREFIX}-buttons`
}

const Root = styled('div')(({ theme }) => ({
  [`&.${classes.root}`]: {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing(2),
    marginTop: theme.spacing(2)
  },
  [`& .${classes.formControl}`]: {
    minWidth: 200
  },
  [`& .${classes.row}`]: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing(2),
    alignItems: 'center'
  },
  [`& .${classes.yearInputs}`]: {
    display: 'flex',
    gap: theme.spacing(1),
    alignItems: 'center'
  },
  [`& .${classes.yearField}`]: {
    width: 100
  },
  [`& .${classes.buttons}`]: {
    display: 'flex',
    gap: theme.spacing(2),
    marginTop: theme.spacing(1)
  }
}))

interface Props {
  variable: WeatherVariable
  aggregation: AggregationPeriod
  referencePeriod: ReferencePeriod
  comparisonYear: number
  onVariableChange: (variable: WeatherVariable) => void
  onAggregationChange: (aggregation: AggregationPeriod) => void
  onReferencePeriodChange: (period: ReferencePeriod) => void
  onComparisonYearChange: (year: number) => void
  onFetch: () => void
  onReset: () => void
  fetchDisabled: boolean
  loading: boolean
}

const ClimatologyControls: React.FC<Props> = ({
  variable,
  aggregation,
  referencePeriod,
  comparisonYear,
  onVariableChange,
  onAggregationChange,
  onReferencePeriodChange,
  onComparisonYearChange,
  onFetch,
  onReset,
  fetchDisabled,
  loading
}) => {
  const handleVariableChange = (event: SelectChangeEvent) => {
    onVariableChange(event.target.value as WeatherVariable)
  }

  const handleAggregationChange = (_: React.MouseEvent<HTMLElement>, value: AggregationPeriod | null) => {
    if (value) {
      onAggregationChange(value)
    }
  }

  const handleReferencePeriodPresetChange = (event: SelectChangeEvent) => {
    const [start, end] = event.target.value.split('-').map(Number)
    onReferencePeriodChange({ start_year: start, end_year: end })
  }

  const handleStartYearChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const year = parseInt(event.target.value, 10)
    if (!isNaN(year)) {
      onReferencePeriodChange({ ...referencePeriod, start_year: year })
    }
  }

  const handleEndYearChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const year = parseInt(event.target.value, 10)
    if (!isNaN(year)) {
      onReferencePeriodChange({ ...referencePeriod, end_year: year })
    }
  }

  const handleComparisonYearChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const year = parseInt(event.target.value, 10)
    if (!isNaN(year)) {
      onComparisonYearChange(year)
    }
  }

  const currentPresetValue = `${referencePeriod.start_year}-${referencePeriod.end_year}`
  const isStandardPeriod = STANDARD_REFERENCE_PERIODS.some(
    p => p.start_year === referencePeriod.start_year && p.end_year === referencePeriod.end_year
  )

  return (
    <Root className={classes.root}>
      <div className={classes.row}>
        <FormControl className={classes.formControl} size="small">
          <InputLabel id="variable-select-label">Variable</InputLabel>
          <Select
            labelId="variable-select-label"
            id="variable-select"
            data-testid="climatology-variable-select"
            value={variable}
            label="Variable"
            onChange={handleVariableChange}
          >
            {Object.values(WeatherVariable).map(v => (
              <MenuItem key={v} value={v}>
                {WEATHER_VARIABLE_LABELS[v]}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <ToggleButtonGroup
          value={aggregation}
          exclusive
          onChange={handleAggregationChange}
          aria-label="aggregation period"
          size="small"
        >
          <ToggleButton value={AggregationPeriod.DAILY} aria-label="daily" data-testid="aggregation-daily">
            Daily
          </ToggleButton>
          <ToggleButton value={AggregationPeriod.MONTHLY} aria-label="monthly" data-testid="aggregation-monthly">
            Monthly
          </ToggleButton>
        </ToggleButtonGroup>
      </div>

      <div className={classes.row}>
        <FormControl className={classes.formControl} size="small">
          <InputLabel id="reference-period-label">Reference Period</InputLabel>
          <Select
            labelId="reference-period-label"
            id="reference-period-select"
            data-testid="reference-period-select"
            value={isStandardPeriod ? currentPresetValue : 'custom'}
            label="Reference Period"
            onChange={handleReferencePeriodPresetChange}
          >
            {STANDARD_REFERENCE_PERIODS.map(p => (
              <MenuItem key={`${p.start_year}-${p.end_year}`} value={`${p.start_year}-${p.end_year}`}>
                {p.start_year} - {p.end_year}
              </MenuItem>
            ))}
            {!isStandardPeriod && (
              <MenuItem value="custom">
                Custom ({referencePeriod.start_year} - {referencePeriod.end_year})
              </MenuItem>
            )}
          </Select>
        </FormControl>

        <Box className={classes.yearInputs}>
          <TextField
            className={classes.yearField}
            label="Start Year"
            type="number"
            size="small"
            value={referencePeriod.start_year}
            onChange={handleStartYearChange}
            inputProps={{ min: 1950, max: 2100 }}
          />
          <span>to</span>
          <TextField
            className={classes.yearField}
            label="End Year"
            type="number"
            size="small"
            value={referencePeriod.end_year}
            onChange={handleEndYearChange}
            inputProps={{ min: 1950, max: 2100 }}
          />
        </Box>
      </div>

      <div className={classes.row}>
        <TextField
          className={classes.yearField}
          label="Compare Year"
          type="number"
          size="small"
          value={comparisonYear}
          onChange={handleComparisonYearChange}
          inputProps={{ min: 1950, max: 2100 }}
          helperText="Year to compare against normals"
        />
      </div>

      <div className={classes.buttons}>
        <Button
          variant="contained"
          color="primary"
          onClick={onFetch}
          disabled={fetchDisabled || loading}
          data-testid="fetch-climatology-btn"
        >
          {loading ? 'Loading...' : 'Fetch Data'}
        </Button>
        <Button variant="outlined" onClick={onReset} data-testid="reset-climatology-btn">
          Reset
        </Button>
      </div>
    </Root>
  )
}

export default React.memo(ClimatologyControls)
