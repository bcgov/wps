import React, { useEffect, useMemo, useRef } from 'react'
import { styled } from '@mui/material/styles'
import { Typography, Paper, Box, IconButton, Tooltip, Menu, MenuItem, ListItemIcon, ListItemText } from '@mui/material'
import { LineChartPro } from '@mui/x-charts-pro/LineChartPro'
import { useChartProApiRef } from '@mui/x-charts-pro/hooks'
import { useTheme } from '@mui/material/styles'
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap'
import SaveAltIcon from '@mui/icons-material/SaveAlt'
import ImageIcon from '@mui/icons-material/Image'
import TableChartIcon from '@mui/icons-material/TableChart'

import {
  AggregationPeriod,
  ClimatologyDataPoint,
  MultiYearClimatologyResult,
  ComparisonYearDataPoint,
  WEATHER_VARIABLE_LABELS,
  WEATHER_VARIABLE_UNITS,
  YearData
} from '../interfaces'

const PREFIX = 'ClimatologyChart'

const classes = {
  root: `${PREFIX}-root`,
  header: `${PREFIX}-header`,
  chartContainer: `${PREFIX}-chartContainer`,
  legend: `${PREFIX}-legend`,
  legendItem: `${PREFIX}-legendItem`,
  legendColor: `${PREFIX}-legendColor`,
  title: `${PREFIX}-title`,
  noData: `${PREFIX}-noData`
}

const Root = styled(Paper)(({ theme }) => ({
  [`&.${classes.root}`]: {
    padding: theme.spacing(2),
    marginTop: theme.spacing(2)
  },
  [`& .${classes.header}`]: {
    position: 'relative',
    marginBottom: theme.spacing(2)
  },
  [`& .${classes.chartContainer}`]: {
    width: '100%',
    height: 450
  },
  [`& .${classes.legend}`]: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing(2),
    justifyContent: 'center',
    marginTop: theme.spacing(1)
  },
  [`& .${classes.legendItem}`]: {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing(0.5)
  },
  [`& .${classes.legendColor}`]: {
    width: 16,
    height: 16,
    borderRadius: 2
  },
  [`& .${classes.title}`]: {
    marginBottom: theme.spacing(2),
    textAlign: 'center'
  },
  [`& .${classes.noData}`]: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: 300,
    color: theme.palette.text.secondary
  }
}))

interface Props {
  data: MultiYearClimatologyResult | null
  loading: boolean
}

// Color palette for multiple years
const YEAR_COLORS = [
  '#e53935', // Red
  '#8e24aa', // Purple
  '#43a047', // Green
  '#fb8c00', // Orange
  '#00acc1', // Cyan
  '#5e35b1', // Deep Purple
  '#d81b60', // Pink
  '#7cb342' // Light Green
]

const ClimatologyChart: React.FC<Props> = ({ data, loading }) => {
  const theme = useTheme()
  const apiRef = useChartProApiRef<'line'>()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const [saveMenuAnchor, setSaveMenuAnchor] = React.useState<null | HTMLElement>(null)

  const handleSaveMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setSaveMenuAnchor(event.currentTarget)
  }

  const handleSaveMenuClose = () => {
    setSaveMenuAnchor(null)
  }

  const handleExportImage = async () => {
    handleSaveMenuClose()
    if (!chartContainerRef.current || !data) return

    const svg = chartContainerRef.current.querySelector('svg')
    if (!svg) return

    const svgData = new XMLSerializer().serializeToString(svg)
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    img.onload = () => {
      canvas.width = img.width
      canvas.height = img.height
      ctx?.drawImage(img, 0, 0)
      const pngUrl = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `climatology_${data.station.code}_${data.variable}.png`
      link.href = pngUrl
      link.click()
    }

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
  }

  const handleExportCSV = () => {
    handleSaveMenuClose()
    if (!data) return

    const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    const isMonthly = data.aggregation === AggregationPeriod.MONTHLY

    // Create CSV header with all comparison years
    const headers = ['Period', 'P10', 'P25', 'P50', 'P75', 'P90']
    data.comparison_years.forEach(year => {
      headers.push(String(year))
    })

    // Create maps for each year's data lookup
    const yearMaps = data.years_data.map((yearData: YearData) => {
      const map = new Map<number, number | null>()
      yearData.data.forEach((point: ComparisonYearDataPoint) => {
        map.set(point.period, point.value)
      })
      return { year: yearData.year, map }
    })

    // Create CSV rows
    const rows = data.climatology.map((point: ClimatologyDataPoint) => {
      const periodLabel = isMonthly ? monthLabels[point.period - 1] : `Day ${point.period}`
      const row: (string | number | null)[] = [periodLabel, point.p10, point.p25, point.p50, point.p75, point.p90]
      yearMaps.forEach(({ map }) => {
        row.push(map.get(point.period) ?? '')
      })
      return row.join(',')
    })

    const csvContent = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    const yearsStr = data.comparison_years.join('-')
    link.download = `climatology_${data.station.code}_${data.variable}_${yearsStr}.csv`
    link.click()
  }

  // Chart colors - gradient from light to dark for percentiles
  const colors = useMemo(
    () => ({
      p10: 'rgba(33, 150, 243, 0.3)', // Lightest
      p25: 'rgba(33, 150, 243, 0.5)',
      p50: 'rgba(33, 150, 243, 0.7)',
      p75: 'rgba(33, 150, 243, 0.85)',
      p90: theme.palette.primary.main, // Darkest
      currentYear: theme.palette.error.main
    }),
    [theme]
  )

  // Process chart data
  const chartData = useMemo(() => {
    if (!data || data.climatology.length === 0) return null

    const xAxisData: number[] = []
    const p10Data: (number | null)[] = []
    const p25Data: (number | null)[] = []
    const p50Data: (number | null)[] = []
    const p75Data: (number | null)[] = []
    const p90Data: (number | null)[] = []

    // Create maps for each year's data lookup
    const yearMaps = data.years_data.map((yearData: YearData) => {
      const map = new Map<number, number | null>()
      yearData.data.forEach((point: ComparisonYearDataPoint) => {
        map.set(point.period, point.value)
      })
      return { year: yearData.year, map }
    })

    // Initialize arrays for each year
    const yearsData: { year: number; data: (number | null)[] }[] = data.comparison_years.map(year => ({
      year,
      data: []
    }))

    // Track extent of comparison year data
    let minDataIndex: number | null = null
    let maxDataIndex: number | null = null

    data.climatology.forEach((point: ClimatologyDataPoint, idx: number) => {
      xAxisData.push(point.period)
      p10Data.push(point.p10)
      p25Data.push(point.p25)
      p50Data.push(point.p50)
      p75Data.push(point.p75)
      p90Data.push(point.p90)

      // Add data for each comparison year and track extent
      let hasAnyYearData = false
      yearMaps.forEach((yearMap, yearIdx) => {
        const value = yearMap.map.get(point.period) ?? null
        yearsData[yearIdx].data.push(value)
        if (value !== null) {
          hasAnyYearData = true
        }
      })

      if (hasAnyYearData) {
        if (minDataIndex === null) minDataIndex = idx
        maxDataIndex = idx
      }
    })

    // Calculate zoom percentages based on comparison year data extent
    const totalPoints = xAxisData.length
    let zoomStart = 0
    let zoomEnd = 100
    if (minDataIndex !== null && maxDataIndex !== null && totalPoints > 0 && data.comparison_years.length > 0) {
      // Add a small padding (5% of range or 5 points, whichever is smaller)
      const padding = Math.min(Math.floor(totalPoints * 0.02), 5)
      const paddedMin = Math.max(0, minDataIndex - padding)
      const paddedMax = Math.min(totalPoints - 1, maxDataIndex + padding)
      zoomStart = (paddedMin / (totalPoints - 1)) * 100
      zoomEnd = (paddedMax / (totalPoints - 1)) * 100
    }

    return {
      xAxisData,
      p10Data,
      p25Data,
      p50Data,
      p75Data,
      p90Data,
      yearsData,
      initialZoom: { start: zoomStart, end: zoomEnd }
    }
  }, [data])

  // Set initial zoom to comparison year data extent
  useEffect(() => {
    if (chartData?.initialZoom && apiRef.current) {
      apiRef.current.setZoomData([
        { axisId: 'x-axis', start: chartData.initialZoom.start, end: chartData.initialZoom.end }
      ])
    }
  }, [chartData, apiRef])

  const handleResetZoom = () => {
    if (chartData?.initialZoom) {
      apiRef.current?.setZoomData([
        { axisId: 'x-axis', start: chartData.initialZoom.start, end: chartData.initialZoom.end }
      ])
    } else {
      apiRef.current?.setZoomData([{ axisId: 'x-axis', start: 0, end: 100 }])
    }
  }

  if (loading) {
    return (
      <Root className={classes.root}>
        <div className={classes.noData}>Loading climatology data...</div>
      </Root>
    )
  }

  if (!data || !chartData) {
    return (
      <Root className={classes.root}>
        <div className={classes.noData}>Select a station and click "Fetch Data" to view climatology chart</div>
      </Root>
    )
  }

  const variableLabel = WEATHER_VARIABLE_LABELS[data.variable]
  const variableUnit = WEATHER_VARIABLE_UNITS[data.variable]
  const xAxisLabel = data.aggregation === AggregationPeriod.DAILY ? 'Day of Year' : 'Month'
  const yAxisLabel = variableUnit ? `${variableLabel} (${variableUnit})` : variableLabel

  // Generate x-axis tick values for monthly view
  const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const isMonthly = data.aggregation === AggregationPeriod.MONTHLY

  // Generate series for each comparison year
  const yearSeries = chartData.yearsData.map((yearData, idx) => ({
    data: yearData.data,
    label: `${yearData.year}`,
    color: YEAR_COLORS[idx % YEAR_COLORS.length],
    showMark: true
  }))

  return (
    <Root className={classes.root}>
      <Box className={classes.header}>
        <Typography variant="h6" className={classes.title}>
          {variableLabel} - {data.station.name} ({data.station.code})
          <Typography variant="body2" color="textSecondary">
            Reference Period: {data.reference_period.start_year} - {data.reference_period.end_year}
            {data.comparison_years.length > 0 && ` | Comparing: ${data.comparison_years.join(', ')}`}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Scroll to zoom, drag to pan
          </Typography>
        </Typography>
        <Box sx={{ position: 'absolute', top: 0, right: 0, display: 'flex', gap: 0.5 }}>
          <Tooltip title="Zoom to comparison data">
            <IconButton size="small" onClick={handleResetZoom}>
              <ZoomOutMapIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Save chart">
            <IconButton size="small" onClick={handleSaveMenuOpen}>
              <SaveAltIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Menu
          anchorEl={saveMenuAnchor}
          open={Boolean(saveMenuAnchor)}
          onClose={handleSaveMenuClose}
        >
          <MenuItem onClick={handleExportImage}>
            <ListItemIcon>
              <ImageIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Save as PNG</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleExportCSV}>
            <ListItemIcon>
              <TableChartIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Export data as CSV</ListItemText>
          </MenuItem>
        </Menu>
      </Box>

      <div className={classes.chartContainer} ref={chartContainerRef}>
        <LineChartPro
          apiRef={apiRef}
          xAxis={[
            {
              id: 'x-axis',
              data: chartData.xAxisData,
              label: xAxisLabel,
              scaleType: 'linear',
              tickMinStep: isMonthly ? 1 : 30,
              valueFormatter: isMonthly
                ? (value: number) => monthLabels[Math.round(value) - 1] || ''
                : undefined,
              zoom: true
            }
          ]}
          yAxis={[
            {
              label: yAxisLabel
            }
          ]}
          series={[
            {
              data: chartData.p10Data,
              label: '10th',
              color: colors.p10,
              showMark: false
            },
            {
              data: chartData.p25Data,
              label: '25th',
              color: colors.p25,
              showMark: false
            },
            {
              data: chartData.p50Data,
              label: '50th (Median)',
              color: colors.p50,
              showMark: false
            },
            {
              data: chartData.p75Data,
              label: '75th',
              color: colors.p75,
              showMark: false
            },
            {
              data: chartData.p90Data,
              label: '90th',
              color: colors.p90,
              showMark: false
            },
            // Comparison year overlays
            ...yearSeries
          ]}
          height={400}
          margin={{ left: 70, right: 20, top: 20, bottom: 50 }}
          hideLegend
        />
      </div>

      <Box className={classes.legend}>
        <div className={classes.legendItem}>
          <div className={classes.legendColor} style={{ backgroundColor: colors.p10 }} />
          <Typography variant="body2">10th</Typography>
        </div>
        <div className={classes.legendItem}>
          <div className={classes.legendColor} style={{ backgroundColor: colors.p25 }} />
          <Typography variant="body2">25th</Typography>
        </div>
        <div className={classes.legendItem}>
          <div className={classes.legendColor} style={{ backgroundColor: colors.p50 }} />
          <Typography variant="body2">50th (Median)</Typography>
        </div>
        <div className={classes.legendItem}>
          <div className={classes.legendColor} style={{ backgroundColor: colors.p75 }} />
          <Typography variant="body2">75th</Typography>
        </div>
        <div className={classes.legendItem}>
          <div className={classes.legendColor} style={{ backgroundColor: colors.p90 }} />
          <Typography variant="body2">90th</Typography>
        </div>
        {chartData.yearsData.map((yearData, idx) => (
          <div key={yearData.year} className={classes.legendItem}>
            <div
              className={classes.legendColor}
              style={{ backgroundColor: YEAR_COLORS[idx % YEAR_COLORS.length] }}
            />
            <Typography variant="body2">{yearData.year}</Typography>
          </div>
        ))}
      </Box>
    </Root>
  )
}

export default React.memo(ClimatologyChart)
