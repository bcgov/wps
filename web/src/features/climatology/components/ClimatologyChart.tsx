import React, { useMemo } from 'react'
import { styled } from '@mui/material/styles'
import { Typography, Paper, Box } from '@mui/material'
import { LineChart } from '@mui/x-charts/LineChart'
import { useTheme } from '@mui/material/styles'

import {
  AggregationPeriod,
  ClimatologyDataPoint,
  ClimatologyResponse,
  CurrentYearDataPoint,
  WEATHER_VARIABLE_LABELS,
  WEATHER_VARIABLE_UNITS
} from '../interfaces'

const PREFIX = 'ClimatologyChart'

const classes = {
  root: `${PREFIX}-root`,
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
  data: ClimatologyResponse | null
  loading: boolean
}

const ClimatologyChart: React.FC<Props> = ({ data, loading }) => {
  const theme = useTheme()

  // Chart colors
  const colors = useMemo(
    () => ({
      band10_90: 'rgba(33, 150, 243, 0.15)', // Light blue band (10th-90th)
      band25_75: 'rgba(33, 150, 243, 0.3)', // Medium blue band (25th-75th)
      mean: theme.palette.primary.main, // Blue mean line
      currentYear: theme.palette.error.main // Red current year line
    }),
    [theme]
  )

  // Process chart data
  const chartData = useMemo(() => {
    if (!data || data.climatology.length === 0) return null

    const xAxisData: number[] = []
    const meanData: (number | null)[] = []
    const p10Data: (number | null)[] = []
    const p25Data: (number | null)[] = []
    const p75Data: (number | null)[] = []
    const p90Data: (number | null)[] = []
    const currentYearData: (number | null)[] = []

    // Create a map for current year data lookup
    const currentYearMap = new Map<number, number | null>()
    data.current_year.forEach((point: CurrentYearDataPoint) => {
      currentYearMap.set(point.period, point.value)
    })

    data.climatology.forEach((point: ClimatologyDataPoint) => {
      xAxisData.push(point.period)
      meanData.push(point.mean)
      p10Data.push(point.p10)
      p25Data.push(point.p25)
      p75Data.push(point.p75)
      p90Data.push(point.p90)
      currentYearData.push(currentYearMap.get(point.period) ?? null)
    })

    return {
      xAxisData,
      meanData,
      p10Data,
      p25Data,
      p75Data,
      p90Data,
      currentYearData
    }
  }, [data])

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

  return (
    <Root className={classes.root}>
      <Typography variant="h6" className={classes.title}>
        {variableLabel} - {data.station.name} ({data.station.code})
        <Typography variant="body2" color="textSecondary">
          Reference Period: {data.reference_period.start_year} - {data.reference_period.end_year}
          {data.comparison_year && ` | Comparison Year: ${data.comparison_year}`}
        </Typography>
      </Typography>

      <div className={classes.chartContainer}>
        <LineChart
          xAxis={[
            {
              data: chartData.xAxisData,
              label: xAxisLabel,
              scaleType: 'linear',
              tickMinStep: data.aggregation === AggregationPeriod.MONTHLY ? 1 : 30,
              valueFormatter:
                data.aggregation === AggregationPeriod.MONTHLY
                  ? value => monthLabels[Math.round(value) - 1] || ''
                  : undefined
            }
          ]}
          yAxis={[
            {
              label: yAxisLabel
            }
          ]}
          series={[
            // 10th percentile (bottom of outer band)
            {
              data: chartData.p10Data,
              label: '10th Percentile',
              color: colors.band10_90,
              showMark: false,
              area: false
            },
            // 90th percentile (top of outer band)
            {
              data: chartData.p90Data,
              label: '90th Percentile',
              color: colors.band10_90,
              showMark: false,
              area: false
            },
            // 25th percentile (bottom of inner band)
            {
              data: chartData.p25Data,
              label: '25th Percentile',
              color: colors.band25_75,
              showMark: false,
              area: false
            },
            // 75th percentile (top of inner band)
            {
              data: chartData.p75Data,
              label: '75th Percentile',
              color: colors.band25_75,
              showMark: false,
              area: false
            },
            // Mean line
            {
              data: chartData.meanData,
              label: 'Mean',
              color: colors.mean,
              showMark: false
            },
            // Current year overlay
            ...(data.comparison_year
              ? [
                  {
                    data: chartData.currentYearData,
                    label: `${data.comparison_year}`,
                    color: colors.currentYear,
                    showMark: true
                  }
                ]
              : [])
          ]}
          height={400}
          margin={{ left: 70, right: 20, top: 20, bottom: 50 }}
          hideLegend
        />
      </div>

      <Box className={classes.legend}>
        <div className={classes.legendItem}>
          <div className={classes.legendColor} style={{ backgroundColor: colors.band10_90 }} />
          <Typography variant="body2">10th-90th Percentile</Typography>
        </div>
        <div className={classes.legendItem}>
          <div className={classes.legendColor} style={{ backgroundColor: colors.band25_75 }} />
          <Typography variant="body2">25th-75th Percentile</Typography>
        </div>
        <div className={classes.legendItem}>
          <div className={classes.legendColor} style={{ backgroundColor: colors.mean }} />
          <Typography variant="body2">Mean</Typography>
        </div>
        {data.comparison_year && (
          <div className={classes.legendItem}>
            <div className={classes.legendColor} style={{ backgroundColor: colors.currentYear }} />
            <Typography variant="body2">{data.comparison_year} Observed</Typography>
          </div>
        )}
      </Box>
    </Root>
  )
}

export default React.memo(ClimatologyChart)
