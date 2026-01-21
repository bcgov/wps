import React, { useState } from 'react'
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
  Box,
  Paper,
  Typography,
  Tooltip
} from '@mui/material'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'

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
  container: `${PREFIX}-container`,
  row: `${PREFIX}-row`,
  divider: `${PREFIX}-divider`,
  yearInputs: `${PREFIX}-yearInputs`,
  yearField: `${PREFIX}-yearField`,
  infoIcon: `${PREFIX}-infoIcon`
}

const Root = styled('div')(({ theme }) => ({
  [`&.${classes.root}`]: {
    marginTop: theme.spacing(2)
  },
  [`& .${classes.container}`]: {
    padding: theme.spacing(2),
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing(2),
    alignItems: 'center'
  },
  [`& .${classes.row}`]: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing(2),
    alignItems: 'center'
  },
  [`& .${classes.divider}`]: {
    width: 1,
    height: 32,
    backgroundColor: theme.palette.divider
  },
  [`& .${classes.yearInputs}`]: {
    display: 'flex',
    gap: theme.spacing(1),
    alignItems: 'center'
  },
  [`& .${classes.yearField}`]: {
    width: 90
  },
  [`& .${classes.infoIcon}`]: {
    fontSize: 16,
    color: theme.palette.text.secondary,
    marginLeft: theme.spacing(0.5),
    verticalAlign: 'middle'
  }
}))

interface StationOption {
  name: string
  code: number
}

interface Props {
  stations: StationOption[]
  stationsLoading: boolean
  selectedStationCode: number | null
  onStationChange: (code: number | null) => void
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
  loading: boolean
}

const ClimatologyControls: React.FC<Props> = ({
  stations,
  stationsLoading,
  selectedStationCode,
  onStationChange,
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
  loading
}) => {
  const [useCustomPeriod, setUseCustomPeriod] = useState(false)

  const handleVariableChange = (event: SelectChangeEvent) => {
    onVariableChange(event.target.value as WeatherVariable)
  }

  const handleAggregationChange = (_: React.MouseEvent<HTMLElement>, value: AggregationPeriod | null) => {
    if (value) {
      onAggregationChange(value)
    }
  }

  const handleReferencePeriodPresetChange = (event: SelectChangeEvent) => {
    const value = event.target.value
    if (value === 'custom') {
      setUseCustomPeriod(true)
    } else {
      setUseCustomPeriod(false)
      const [start, end] = value.split('-').map(Number)
      onReferencePeriodChange({ start_year: start, end_year: end })
    }
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

  const handleStationChange = (event: SelectChangeEvent<number | ''>) => {
    const value = event.target.value
    onStationChange(value === '' ? null : (value as number))
  }

  const currentPresetValue = `${referencePeriod.start_year}-${referencePeriod.end_year}`
  const isStandardPeriod = STANDARD_REFERENCE_PERIODS.some(
    p => p.start_year === referencePeriod.start_year && p.end_year === referencePeriod.end_year
  )

  const InfoIcon: React.FC<{ tooltip: string }> = ({ tooltip }) => (
    <Tooltip title={tooltip} arrow>
      <InfoOutlinedIcon className={classes.infoIcon} />
    </Tooltip>
  )

  return (
    <Root className={classes.root}>
      <Paper className={classes.container} variant="outlined">
        {/* Station */}
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel id="station-select-label">
            Station
            <InfoIcon tooltip="Select a weather station to view climatology data" />
          </InputLabel>
          <Select
            labelId="station-select-label"
            id="station-select"
            data-testid="climatology-station-select"
            value={selectedStationCode ?? ''}
            label="Station"
            onChange={handleStationChange}
            disabled={stationsLoading}
          >
            {stations.map(s => (
              <MenuItem key={s.code} value={s.code}>
                {s.name} ({s.code})
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <div className={classes.divider} />

        {/* Variable */}
        <FormControl size="small" sx={{ minWidth: 180 }}>
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

        {/* Aggregation */}
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

        <div className={classes.divider} />

        {/* Reference Period */}
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel id="reference-period-label">
            Reference
            <InfoIcon tooltip="Historical baseline period for calculating climate normals" />
          </InputLabel>
          <Select
            labelId="reference-period-label"
            id="reference-period-select"
            data-testid="reference-period-select"
            value={useCustomPeriod ? 'custom' : (isStandardPeriod ? currentPresetValue : 'custom')}
            label="Reference"
            onChange={handleReferencePeriodPresetChange}
          >
            {STANDARD_REFERENCE_PERIODS.map(p => (
              <MenuItem key={`${p.start_year}-${p.end_year}`} value={`${p.start_year}-${p.end_year}`}>
                {p.start_year}-{p.end_year}
              </MenuItem>
            ))}
            <MenuItem value="custom">Custom</MenuItem>
          </Select>
        </FormControl>

        {(useCustomPeriod || !isStandardPeriod) && (
          <Box className={classes.yearInputs}>
            <TextField
              className={classes.yearField}
              label="Start"
              type="number"
              size="small"
              value={referencePeriod.start_year}
              onChange={handleStartYearChange}
              inputProps={{ min: 1950, max: 2100 }}
            />
            <Typography variant="body2" color="textSecondary">
              –
            </Typography>
            <TextField
              className={classes.yearField}
              label="End"
              type="number"
              size="small"
              value={referencePeriod.end_year}
              onChange={handleEndYearChange}
              inputProps={{ min: 1950, max: 2100 }}
            />
          </Box>
        )}

        {/* Comparison Year */}
        <TextField
          className={classes.yearField}
          label="Compare"
          type="number"
          size="small"
          value={comparisonYear}
          onChange={handleComparisonYearChange}
          inputProps={{ min: 1950, max: 2100 }}
          InputProps={{
            endAdornment: <InfoIcon tooltip="Year to overlay on the chart for comparison against historical normals" />
          }}
        />

        <div className={classes.divider} />

        {/* Actions */}
        <Button
          variant="contained"
          color="primary"
          onClick={onFetch}
          disabled={selectedStationCode === null || loading}
          data-testid="fetch-climatology-btn"
        >
          {loading ? 'Loading...' : 'Fetch'}
        </Button>
        <Button variant="outlined" onClick={onReset} data-testid="reset-climatology-btn" size="small">
          Reset
        </Button>
      </Paper>
    </Root>
  )
}

export default React.memo(ClimatologyControls)
