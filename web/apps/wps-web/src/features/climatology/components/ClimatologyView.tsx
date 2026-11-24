import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  ToggleButton,
  ToggleButtonGroup,
  Typography
} from '@mui/material'
import {
  type ClimatologyMethod,
  type ClimatologyVariable,
  type DailyClimatology,
  getDailyClimatology
} from '@wps/api/climatologyAPI'
import { maxBy, range } from 'lodash'
import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  buildClimatologyRows,
  CLIMATOLOGY_VARIABLES,
  type DateWindow,
  FIRE_SEASON,
  FULL_YEAR,
  formatDay,
  rowsExtent,
  todayOnChart,
  valueExtent,
  variableInSentence,
  visibleWindow
} from '@/features/climatology/climatologyRows'
import {
  type ComparedYear,
  chooseComparedYears,
  MAX_COMPARED_YEARS,
  MAX_COMPARED_YEARS_EACH
} from '@/features/climatology/comparedYears'
import ClimatologyChart from '@/features/climatology/components/ClimatologyChart'
import ClimatologyLegend from '@/features/climatology/components/ClimatologyLegend'
import ClimatologyTimeline from '@/features/climatology/components/ClimatologyTimeline'
import ComparedYearsPicker from '@/features/climatology/components/ComparedYearsPicker'
import type { StationOption } from '@/features/climatology/stationGroups'

// The data mart's first year of station observations.
const FIRST_YEAR = 1987
// The most stations the API combines in one request.
export const MAX_STATIONS = 150

type Season = 'fire-season' | 'full-year'

const METHOD_DESCRIPTIONS: Record<ClimatologyMethod, string> = {
  average:
    "Each day is the mean of the stations that reported it, and the bands are those means' spread over the years.",
  pooled:
    'The bands are the spread of every station’s values over the years, and the line is the mean of the stations.',
  each: 'Each station is compared with its own history, on one shared scale.'
}

export interface ClimatologyViewProps {
  stations: StationOption[]
  // The name of the group the stations were chosen as, if they were.
  groupLabel: string | null
  // What to say before any station is chosen: how to choose them differs by page.
  emptyMessage: string
}

/** The controls and charts of a climatology for the stations chosen. */
const ClimatologyView = ({ stations, groupLabel, emptyMessage }: ClimatologyViewProps) => {
  const currentYear = new Date().getFullYear()
  const [variable, setVariable] = useState<ClimatologyVariable>('temperature')
  const [year, setYear] = useState(currentYear)
  const [season, setSeason] = useState<Season>('fire-season')
  const [method, setMethod] = useState<ClimatologyMethod>('average')
  // The years chosen to compare with, of which charts of each station show the newest.
  const [chosenYears, setChosenYears] = useState<ComparedYear[]>([])
  const [highlighted, setHighlighted] = useState<number | null>(null)
  const [climatology, setClimatology] = useState<DailyClimatology | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // The dates chosen by zooming or with the timeline; null shows every day.
  const [chosenWindow, setChosenWindow] = useState<DateWindow | null>(null)

  const stationNames = useMemo(() => new Map(stations.map(station => [station.code, station.name])), [stations])
  const stationCodes = useMemo(() => stations.map(station => station.code), [stations])
  const tooManyStations = stationCodes.length > MAX_STATIONS
  // One station is the same whichever way it is combined.
  const effectiveMethod: ClimatologyMethod = stationCodes.length > 1 ? method : 'average'

  const compareLimit = effectiveMethod === 'each' ? MAX_COMPARED_YEARS_EACH : MAX_COMPARED_YEARS
  const comparedYears = useMemo(
    () => chosenYears.filter(each => each.year !== year).slice(0, compareLimit),
    [chosenYears, year, compareLimit]
  )
  const compareYears = useMemo(() => comparedYears.map(each => each.year), [comparedYears])
  // A year that is no longer compared does not stay highlighted.
  const highlightedYear = compareYears.find(each => each === highlighted) ?? null
  const onCompareYears = useCallback(
    (chosen: number[]) => setChosenYears(current => chooseComparedYears(current, chosen)),
    []
  )

  useEffect(() => {
    if (stationCodes.length === 0 || tooManyStations) {
      setClimatology(null)
      return
    }
    // A response that arrives after the selection has changed again is dropped.
    let current = true
    setLoading(true)
    setError(null)
    getDailyClimatology(stationCodes, variable, year, effectiveMethod, compareYears)
      .then(result => {
        if (current) {
          setClimatology(result)
        }
      })
      .catch(() => {
        if (current) {
          setClimatology(null)
          setError('The climatology for these stations could not be loaded.')
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
  }, [stationCodes, tooManyStations, variable, year, effectiveMethod, compareYears])

  const monthRange = season === 'fire-season' ? FIRE_SEASON : FULL_YEAR
  const charts = useMemo(
    () =>
      (climatology?.series ?? []).map(series => ({
        series,
        rows: buildClimatologyRows(series, climatology?.year ?? year, monthRange)
      })),
    [climatology, year, monthRange]
  )
  const chartsWithRows = charts.filter(chart => chart.rows.length > 0)
  // The timeline and the zoom span the chart with the most days.
  const longestRows = useMemo(() => maxBy(charts, chart => chart.rows.length)?.rows ?? [], [charts])
  const extent = useMemo(() => rowsExtent(longestRows), [longestRows])
  // A window chosen for other rows, such as another year or other months, shows every day again.
  const dateWindow = useMemo(() => (extent ? visibleWindow(chosenWindow, extent) : null), [chosenWindow, extent])
  const showsEveryDay =
    extent === null || dateWindow === null || (dateWindow.start === extent.start && dateWindow.end === extent.end)
  const onDateWindowChange = useCallback((next: DateWindow) => setChosenWindow(next), [])
  // Charts of several stations share one y axis, so they compare at a glance.
  const yDomain = useMemo(
    () => (chartsWithRows.length > 1 ? valueExtent(chartsWithRows.flatMap(chart => chart.rows)) : undefined),
    [chartsWithRows]
  )
  const today = useMemo(() => todayOnChart(longestRows, year), [longestRows, year])
  const years = useMemo(() => range(currentYear, FIRST_YEAR - 1, -1), [currentYear])

  const variableLabel = variableInSentence(variable)
  const combined = effectiveMethod !== 'each' && stationCodes.length > 1
  const subject = groupLabel ?? (stations.length === 1 ? stations[0].name : `${stations.length} stations`)
  const referenceYears = (() => {
    const firsts = charts.flatMap(chart => chart.series.first_reference_year ?? [])
    const lasts = charts.flatMap(chart => chart.series.last_reference_year ?? [])
    return firsts.length > 0 ? `${Math.min(...firsts)} to ${Math.max(...lasts)}` : null
  })()

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
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
        <ComparedYearsPicker
          year={year}
          years={years}
          compared={compareYears}
          limit={compareLimit}
          onChange={onCompareYears}
        />
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
        {stationCodes.length > 1 && (
          <ToggleButtonGroup
            size="small"
            exclusive
            value={method}
            onChange={(_, selected: ClimatologyMethod | null) => selected && setMethod(selected)}
            aria-label="How stations are combined"
          >
            <ToggleButton value="average">Average</ToggleButton>
            <ToggleButton value="pooled">Pooled</ToggleButton>
            <ToggleButton value="each">Each station</ToggleButton>
          </ToggleButtonGroup>
        )}
        {loading && <CircularProgress size={24} aria-label="Loading climatology" />}
      </Box>

      {error && <Alert severity="error">{error}</Alert>}
      {tooManyStations && (
        <Alert severity="warning">
          Choose at most {MAX_STATIONS} stations. {stations.length} are chosen.
        </Alert>
      )}
      {stations.length === 0 && <Typography color="text.secondary">{emptyMessage}</Typography>}
      {climatology !== null && chartsWithRows.length === 0 && !loading && (
        <Alert severity="info">
          {subject} {stations.length === 1 ? 'has' : 'have'} no history of daily {variableLabel} for these months.
        </Alert>
      )}
      {climatology !== null && chartsWithRows.length > 0 && dateWindow !== null && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Typography variant="h6" component="h2">
            {subject}: daily {variableLabel}, {climatology.year}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Noon observations, compared with {referenceYears} excluding {climatology.year}.
            {compareYears.length > 0 &&
              (compareYears.length === 1
                ? ` ${compareYears[0]} is part of that history.`
                : ' The years chosen to compare with are part of that history.')}
            {stationCodes.length > 1 && ` ${METHOD_DESCRIPTIONS[effectiveMethod]}`}
          </Typography>
          <ClimatologyLegend
            yearLabel={combined ? `${climatology.year} (mean of stations)` : `${climatology.year}`}
            comparedYears={comparedYears}
            highlightedYear={highlightedYear}
            onHighlight={setHighlighted}
          />
          {effectiveMethod === 'each' ? (
            charts.map(({ series, rows }) => {
              const name = stationNames.get(series.station_codes[0]) ?? `${series.station_codes[0]}`
              return (
                <Box key={series.station_codes[0]} data-testid="climatology-station-chart">
                  <Typography variant="subtitle1" component="h3">
                    {name} ({series.station_codes[0]})
                  </Typography>
                  {rows.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">
                      No history of daily {variableLabel} for these months.
                    </Typography>
                  ) : (
                    <ClimatologyChart
                      rows={rows}
                      variable={variable}
                      year={climatology.year}
                      dateWindow={dateWindow}
                      onDateWindowChange={onDateWindowChange}
                      comparedYears={comparedYears}
                      highlightedYear={highlightedYear}
                      today={today}
                      yDomain={yDomain}
                      // A plain wheel scrolls past the stack of charts; Control or Command zooms.
                      wheelZoom="modifier"
                      title={name}
                      height={300}
                    />
                  )}
                </Box>
              )
            })
          ) : (
            <ClimatologyChart
              rows={chartsWithRows[0].rows}
              variable={variable}
              year={climatology.year}
              dateWindow={dateWindow}
              onDateWindowChange={onDateWindowChange}
              comparedYears={comparedYears}
              highlightedYear={highlightedYear}
              today={today}
              title={subject}
            />
          )}
          <ClimatologyTimeline
            rows={longestRows}
            year={climatology.year}
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
            Drag the timeline&apos;s handles to choose the dates shown. On the chart,{' '}
            {effectiveMethod === 'each' ? 'hold Control or Command and scroll' : 'scroll'} to zoom and drag to pan; with
            the chart focused, + and − zoom, the arrow keys pan and Home shows every day.
          </Typography>
        </Box>
      )}
    </Box>
  )
}

export default ClimatologyView
