import React from 'react'
// import { makeStyles } from '@material-ui/core/styles'

import { MODEL_VALUE_DECIMAL } from 'utils/constants'
import { PeakValuesResponse, PeakWeekValues, StationPeakValues } from 'api/peakBurninessAPI'
import { Container } from '@material-ui/core'
import { ErrorMessage } from 'components/ErrorMessage'
import { PeakValuesStationResultTable } from 'features/peakBurniness/components/tables/PeakValuesStationResultTable'
import { useSelector } from 'react-redux'
import { selectPeakBurninessValues, selectStations } from 'app/rootReducer'
import { Station } from 'api/stationAPI'
import { GridItem } from 'components'

interface Column {
  id: keyof PeakWeekValues
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

// const useStyles = makeStyles({
//   display: {
//     paddingBottom: 12
//   },
//   paper: {
//     width: '100%'
//   },
//   tableContainer: {
//     maxHeight: 280
//   },
//   title: {
//     paddingBottom: 4
//   },
//   root: {
//     marginTop: 15
//   }
// })

export const PeakValuesResults = React.memo(function _(props: PeakValuesResultsProps) {
  // const classes = useStyles()
  const { stationCodes, stationsByCode, peakValuesByStation } = props

  const stationResults = stationCodes.map(code => {
    const station = stationsByCode[code]
    if (!station) return null

    if (peakValuesByStation === undefined) return null

    if (peakValuesByStation[code] === undefined) return null

    const peakValues: StationPeakValues = {
      code: code,
      weeks: peakValuesByStation[code]
    }

    console.log(peakValues)

    return (
      <GridItem key={code} md lg>
        <PeakValuesStationResultTable stationResponse={peakValues} />
      </GridItem>
    )
  })

  return(
    <Container>
      {stationResults}
    </Container>
  )
})

interface PeakValuesResultsWrapperProps {
  stationCodes: number[]
}

const PeakValuesResultsWrapper: React.FunctionComponent<PeakValuesResultsWrapperProps> = props => {
  const { stationsByCode } = useSelector(selectStations)
  const { peakBurninessValues, error } = useSelector(selectPeakBurninessValues)

  if (error) {
    return (
      <ErrorMessage
        error={error}
        context="while getting the calculation result"
        marginTop={5}
      />
    )
  }

  if (!peakBurninessValues) return null

  return (
    <PeakValuesResults
      stationCodes={props.stationCodes}
      stationsByCode={stationsByCode}
      peakValuesByStation={peakBurninessValues}
    />
  )
}

export default PeakValuesResultsWrapper
