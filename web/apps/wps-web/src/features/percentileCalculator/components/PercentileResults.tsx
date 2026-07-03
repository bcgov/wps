import { styled } from '@mui/material/styles'
import type { PercentilesResponse } from '@wps/api/percentileAPI'
import { ErrorMessage } from '@wps/ui/ErrorMessage'
import { GridContainer, GridItem } from '@wps/ui/Grid'
import { selectPercentiles } from 'app/rootReducer'
import { PercentileCalcDocumentation } from 'features/percentileCalculator/components/PercentileCalcDocumentation'
import { PercentileMeanResultTable } from 'features/percentileCalculator/components/PercentileMeanResultTable'
import { PercentileStationResultTable } from 'features/percentileCalculator/components/PercentileStationResultTable'
import React from 'react'
import { useSelector } from 'react-redux'

const PREFIX = 'PercentileResultsWrapper'

const classes = {
  root: `${PREFIX}-root`,
  gridContainer: `${PREFIX}-gridContainer`
}

interface PercentileResultsProps {
  result: PercentilesResponse
  timeRange: number
}

export const PercentileResults = React.memo(function _(props: PercentileResultsProps) {
  // Object.entries(result.stations) is an array of station code & station response key value pairs
  const stationResults = Object.entries(props.result.stations).map(([stationCode, stationResponse]) => {
    return (
      <GridItem key={stationCode} size={12}>
        <PercentileStationResultTable stationResponse={stationResponse} timeRange={props.timeRange} />
      </GridItem>
    )
  })
  const isMoreThanOneResult = stationResults.length > 1

  return (
    <StyledResultTableContainer data-testid="percentile-result-tables" className={classes.root}>
      <GridContainer className={classes.gridContainer}>
        {isMoreThanOneResult && (
          <GridItem size={12}>
            <PercentileMeanResultTable meanValues={props.result.mean_values} />
          </GridItem>
        )}
        {stationResults}
      </GridContainer>
      <StyledGridContainer className={classes.gridContainer}>
        <GridItem size={12}>
          <PercentileCalcDocumentation />
        </GridItem>
      </StyledGridContainer>
    </StyledResultTableContainer>
  )
})

const StyledGridContainer = styled(GridContainer)({
  marginBottom: 15
})

const StyledResultTableContainer = styled('div')({
  marginTop: 15
})

const PercentileResultsWrapper: React.FC<{ timeRange: number }> = props => {
  const { result, error } = useSelector(selectPercentiles)

  if (error) {
    return <ErrorMessage error={error} context="while getting the calculation result" marginTop={5} />
  }

  if (!result) return null

  return <PercentileResults result={result} timeRange={props.timeRange} />
}

export default PercentileResultsWrapper
