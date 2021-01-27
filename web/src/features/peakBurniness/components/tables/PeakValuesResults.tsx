import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { MODEL_VALUE_DECIMAL } from 'utils/constants'
import { PeakValuesResponse, PeakWeekValues, StationPeakValues } from 'api/peakBurninessAPI'
import { Container } from '@material-ui/core'
import { PeakValuesStationResultTable } from 'features/peakBurniness/components/tables/PeakValuesStationResultTable'
import { useSelector } from 'react-redux'
import { selectPeakBurninessValues, selectStations } from 'app/rootReducer'
import { Station } from 'api/stationAPI'

export interface PeakWeatherValue {
  week: string
  max_temp?: number | null
  min_rh?: number | null
  max_wind_speed?: number | null
  max_ffmc?: number | null
  max_fwi?: number | null
  hour_max_temp?: number | null
  hour_min_rh?: number | null
  hour_max_wind_speed?: number | null
  hour_max_ffmc?: number | null
  hour_max_fwi?: number | null
}

interface Column {
  id: keyof PeakWeatherValue
  label: string
  minWidth?: number
  maxWidth?: number
  align?: 'left' | 'right' | 'center'
  format?: (value: number) => string | number
  formatStr?: (value: string) => string
}

export interface PeakValuesResultsProps {
  stationCodes: number[]
  stationsByCode: Record<number, Station | undefined>
  peakValuesByStation: PeakValuesResponse | undefined
}

export const columns: Column[] = [
  {
    id: 'week',
    label: 'Week',
    align: 'left',
    formatStr: (value: string): string => value
  },
  {
    id: 'max_temp',
    label: 'Max Hourly Temp (°C)',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_max_temp',
    label: 'Hour of Max Temp',
    align: 'right',
    format: (value: number): string => value.toString()
  },
  {
    id: 'min_rh',
    label: 'Min Hourly RH (%)',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_min_rh',
    label: 'Hour of Min RH',
    align: 'right',
    format: (value: number): string => value.toString()
  },
  {
    id: 'max_wind_speed',
    label: 'Max Wind Speed (km/h)',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_max_wind_speed',
    label: 'Hour of Max Wind Speed',
    align: 'right',
    format: (value: number): string => value.toString()
  },
  {
    id: 'max_ffmc',
    label: 'Max FFMC',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_max_ffmc',
    label: 'Hour of Max FFMC',
    align: 'right',
    format: (value: number): string => value.toString()
  },
  {
    id: 'max_fwi',
    label: 'Max FWI',
    align: 'right',
    format: (value: number): string => value.toFixed(MODEL_VALUE_DECIMAL)
  },
  {
    id: 'hour_max_fwi',
    label: 'Hour of Max FWI',
    align: 'right',
    format: (value: number): string => value.toString()
  }
]

const useStyles = makeStyles({
  display: {
    paddingBottom: 12
  },
  paper: {
    width: '100%'
  },
  tableContainer: {
    maxHeight: 280
  },
  title: {
    paddingBottom: 4
  },
  root: {
    marginTop: 15
  }
})

export const PeakValuesResults = React.memo(function _(props: PeakValuesResultsProps) {
  const classes = useStyles()

  const stationResults = props.stationCodes.map(code => {
    const station = props.stationsByCode[code]
    if (!station) return null

    const peakValues: StationPeakValues = {
      'code': code,
      'weeks': props.peakValuesByStation?[code]
    }

    return (
      <Container key={code}>
        <PeakValuesStationResultTable stationResponse={peakValues} />
      </Container>
    )
  })

  return(
    <div>
      {stationResults}
    </div>
  )
})

interface PeakValuesResultsWrapperProps {
  stationCodes: number[]
}

const PeakValuesResultsWrapper: React.FunctionComponent<PeakValuesResultsWrapperProps> = props => {
  const { stationsByCode } = useSelector(selectStations)
  const { peakBurninessValues } = useSelector(selectPeakBurninessValues)

  return (
    <PeakValuesResults
      stationCodes={props.stationCodes}
      stationsByCode={stationsByCode}
      peakValuesByStation={peakBurninessValues}
    />
  )
}

export default PeakValuesResultsWrapper
