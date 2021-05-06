import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { PeakValuesResponse, StationPeakValues } from 'api/peakBurninessAPI'
import { Container } from '@material-ui/core'
import { ErrorMessage } from 'components/ErrorMessage'
import { PeakValuesStationResultTable } from 'features/peakBurniness/components/tables/PeakValuesStationResultTable'
import { PeakBurninessDocumentation } from 'features/peakBurniness/components/PeakBurninessDocumentation'
import { useSelector } from 'react-redux'
import { selectPeakBurninessValues, selectPercentileStations } from 'app/rootReducer'
import { DetailedGeoJsonStation, GeoJsonStation } from 'api/stationAPI'
import { GridItem } from 'components'

export interface PeakValuesResultsProps {
  stationCodes: number[]
  stationsByCode: Record<number, GeoJsonStation | DetailedGeoJsonStation | undefined>
  peakValuesByStation: PeakValuesResponse
}

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
  const { stationCodes, stationsByCode, peakValuesByStation } = props

  const stationResults = stationCodes.map(code => {
    const station = stationsByCode[code]
    if (!station) return null

    if (peakValuesByStation === undefined) {
      return null
    }

    if (peakValuesByStation['stations'][code] === undefined) {
      return null
    }

    const peakValues: StationPeakValues = {
      code: code,
      weeks: peakValuesByStation['stations'][code]
    }

    console.log(peakValues)

    return (
      <GridItem key={code} md lg>
        <PeakValuesStationResultTable stationResponse={peakValues} />
      </GridItem>
    )
  })

  return (
    <Container>
      <PeakBurninessDocumentation />
      {stationResults}
    </Container>
  )
})

interface PeakValuesResultsWrapperProps {
  stationCodes: number[]
}

const PeakValuesResultsWrapper: React.FunctionComponent<PeakValuesResultsWrapperProps> = props => {
  const { stationsByCode } = useSelector(selectPercentileStations)
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

  console.log(peakBurninessValues)
  if (!peakBurninessValues) {
    console.log('asdfkasd;flnasl;dfn empty')
    return null
  }

  return (
    <PeakValuesResults
      stationCodes={props.stationCodes}
      stationsByCode={stationsByCode}
      peakValuesByStation={peakBurninessValues}
    />
  )
}

export default PeakValuesResultsWrapper
