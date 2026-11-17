import {
  Alert,
  Autocomplete,
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography
} from '@mui/material'
import { type ClimatologyVariable, type DailyClimatology, getDailyClimatology } from '@wps/api/climatologyAPI'
import { getStations, StationSource } from '@wps/api/stationAPI'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { CLIMATOLOGY_NAME } from '@wps/utils/constants'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { range, sortBy } from 'lodash'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireWeatherStations } from '@/app/rootReducer'
import type { AppDispatch } from '@/app/store'
import {
  buildClimatologyRows,
  CLIMATOLOGY_VARIABLES,
  type DateWindow,
  FIRE_SEASON,
  FULL_YEAR,
  formatDay,
  rowsExtent,
  todayOnChart,
  visibleWindow
} from '@/features/climatology/climatologyRows'
import ClimatologyChart from '@/features/climatology/components/ClimatologyChart'
import ClimatologyLegend from '@/features/climatology/components/ClimatologyLegend'
import ClimatologyTimeline from '@/features/climatology/components/ClimatologyTimeline'
import Footer from '@/features/landingPage/components/Footer'

// The data mart's first year of station observations.
const FIRST_YEAR = 1987

interface StationOption {
  code: number
  name: string
}

type Season = 'fire-season' | 'full-year'

const ClimatologyPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { stations, error: stationsError } = useSelector(selectFireWeatherStations)

  const currentYear = new Date().getFullYear()
  const [station, setStation] = useState<StationOption | null>(null)
  const [variable, setVariable] = useState<ClimatologyVariable>('temperature')
  const [year, setYear] = useState(currentYear)
  const [season, setSeason] = useState<Season>('fire-season')
  const [climatology, setClimatology] = useState<DailyClimatology | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // The dates chosen by zooming or with the timeline; null shows every day.
  const [chosenWindow, setChosenWindow] = useState<DateWindow | null>(null)

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, [dispatch])

  const stationOptions = useMemo<StationOption[]>(
    () =>
      sortBy(
        stations.map(({ properties }) => ({ code: properties.code, name: properties.name })),
        'name'
      ),
    [stations]
  )

  useEffect(() => {
    if (station === null) {
      setClimatology(null)
      return
    }
    // A response that arrives after the selection has changed again is dropped.
    let current = true
    setLoading(true)
    setError(null)
    getDailyClimatology(station.code, variable, year)
      .then(result => {
        if (current) {
          setClimatology(result)
        }
      })
      .catch(() => {
        if (current) {
          setClimatology(null)
          setError('The climatology for this station could not be loaded.')
        }
      })
      .finally(() => {
        if (current) {
          setLoading(false)
        }
      })
    return () => {
      current = false
    }
  }, [station, variable, year])

  const monthRange = season === 'fire-season' ? FIRE_SEASON : FULL_YEAR
  const rows = useMemo(
    () => (climatology ? buildClimatologyRows(climatology, monthRange) : []),
    [climatology, monthRange]
  )
  const extent = useMemo(() => rowsExtent(rows), [rows])
  // A window chosen for other rows, such as another year or other months, shows every day again.
  const dateWindow = useMemo(() => (extent ? visibleWindow(chosenWindow, extent) : null), [chosenWindow, extent])
  const showsEveryDay =
    extent === null || dateWindow === null || (dateWindow.start === extent.start && dateWindow.end === extent.end)
  const onDateWindowChange = useCallback((next: DateWindow) => setChosenWindow(next), [])
  const today = useMemo(() => todayOnChart(rows, year), [rows, year])
  const years = useMemo(() => range(currentYear, FIRST_YEAR - 1, -1), [currentYear])

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <GeneralHeader isBeta={true} spacing={1} title={CLIMATOLOGY_NAME} />
      <Box sx={{ flex: 1, padding: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
          <Autocomplete
            sx={{ width: 320 }}
            options={stationOptions}
            value={station}
            onChange={(_, selected) => setStation(selected)}
            getOptionLabel={option => `${option.name} (${option.code})`}
            isOptionEqualToValue={(option, selected) => option.code === selected.code}
            renderInput={params => <TextField {...params} label="Weather station" size="small" />}
          />
          <FormControl size="small" sx={{ width: 220 }}>
            <InputLabel id="climatology-variable-label">Variable</InputLabel>
            <Select
              labelId="climatology-variable-label"
              label="Variable"
              value={variable}
              onChange={event => setVariable(event.target.value as ClimatologyVariable)}
            >
              {Object.entries(CLIMATOLOGY_VARIABLES).map(([key, info]) => (
                <MenuItem key={key} value={key}>
                  {info.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ width: 120 }}>
            <InputLabel id="climatology-year-label">Year</InputLabel>
            <Select
              labelId="climatology-year-label"
              label="Year"
              value={year}
              onChange={event => setYear(Number(event.target.value))}
            >
              {years.map(option => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={season}
            onChange={(_, selected: Season | null) => selected && setSeason(selected)}
            aria-label="Months shown"
          >
            <ToggleButton value="fire-season">April to October</ToggleButton>
            <ToggleButton value="full-year">Full year</ToggleButton>
          </ToggleButtonGroup>
          {loading && <CircularProgress size={24} aria-label="Loading climatology" />}
        </Box>

        {stationsError && <Alert severity="error">The list of weather stations could not be loaded.</Alert>}
        {error && <Alert severity="error">{error}</Alert>}
        {station === null && (
          <Typography color="text.secondary">
            Choose a weather station to compare a year of its daily observations with its history.
          </Typography>
        )}
        {station !== null && climatology !== null && rows.length === 0 && !loading && (
          <Alert severity="info">
            {station.name} has no history of daily {CLIMATOLOGY_VARIABLES[variable].label.toLowerCase()} for these
            months.
          </Alert>
        )}
        {station !== null && climatology !== null && rows.length > 0 && dateWindow !== null && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="h6" component="h2">
              {station.name}: daily {CLIMATOLOGY_VARIABLES[variable].label.toLowerCase()}, {year}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Noon observations, compared with {climatology.first_reference_year} to {climatology.last_reference_year}{' '}
              excluding {year}.
            </Typography>
            <ClimatologyLegend year={year} />
            <ClimatologyChart
              rows={rows}
              variable={variable}
              year={year}
              dateWindow={dateWindow}
              onDateWindowChange={onDateWindowChange}
              today={today}
              stationName={station.name}
            />
            <ClimatologyTimeline
              rows={rows}
              year={year}
              dateWindow={dateWindow}
              onDateWindowChange={onDateWindowChange}
            />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body2" role="status" aria-live="polite">
                Showing {formatDay(dateWindow.start)} to {formatDay(dateWindow.end)}
              </Typography>
              <Button size="small" variant="outlined" disabled={showsEveryDay} onClick={() => setChosenWindow(null)}>
                Show every day
              </Button>
            </Box>
            <Typography variant="caption" color="text.secondary">
              Drag the timeline&apos;s handles to choose the dates shown. On the chart, click and then scroll to zoom,
              or drag to pan; with the chart focused, + and − zoom, the arrow keys pan and Home shows every day.
            </Typography>
          </Box>
        )}
      </Box>
      <Footer />
    </Box>
  )
}

export default ClimatologyPage
