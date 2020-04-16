import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { useSelector } from 'react-redux'

import { selectPercentilesReducer } from 'app/rootReducer'
import { PercentileMeanResultTable } from 'features/percentileCalculator/components/PercentileMeanResultTable'
import { PercentileStationResultTable } from 'features/percentileCalculator/components/PercentileStationResultTable'
import { ErrorMessage } from 'components/ErrorMessage'
import { GridItem, GridContainer } from 'components/Grid'
import { PercentileCalcDocumentation } from 'features/percentileCalculator/components/PercentileCalcDocumentation'

const useStyles = makeStyles({
  root: {
    marginTop: 15
  },
  gridContainer: {
    marginBottom: 15
  }
})

export const PercentileResults = () => {
  const classes = useStyles()
  const { result, error } = useSelector(selectPercentilesReducer)

  if (error) {
    return (
      <ErrorMessage message={error} when="while getting the calculation" marginTop={5} />
    )
  }

  if (!result) return null

  // Object.entries(result.stations) is an array of station code & station response key value pairs
  const stationResults = Object.entries(result.stations).map(
    ([stationCode, stationResponse]) => {
      return (
        <GridItem key={stationCode} lg={6}>
          <PercentileStationResultTable stationResponse={stationResponse} />
        </GridItem>
      )
    }
  )
  const isMoreThanOneResult = stationResults.length > 1

  return (
    <div data-testid="percentile-result-tables" className={classes.root}>
      <GridContainer className={classes.gridContainer}>
        {stationResults}
        {isMoreThanOneResult && (
          <GridItem lg={6}>
            <PercentileMeanResultTable meanValues={result.mean_values} />
          </GridItem>
        )}
      </GridContainer>
      <GridContainer className={classes.gridContainer}>
        <GridItem lg={12} md={12}>
          <PercentileCalcDocumentation />
        </GridItem>
      </GridContainer>
    </div>
  )
}
