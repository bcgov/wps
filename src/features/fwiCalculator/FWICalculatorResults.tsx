import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { useSelector } from 'react-redux'

import { selectPercentilesReducer } from 'app/rootReducer'
import { PercentileMeanResultTable } from 'features/fwiCalculator/components/PercentileMeanResultTable'
import { PercentileStationResultTable } from 'features/fwiCalculator/components/PercentileStationResultTable'
import { ErrorMessage } from 'components/ErrorMessage'
import { GridItem, GridContainer } from 'components/Grid'

const useStyles = makeStyles({
  root: {
    marginTop: 15
  }
})

export const FWICalculatorResults = () => {
  const classes = useStyles()
  const { result, error } = useSelector(selectPercentilesReducer)

  if (error) {
    return (
      <ErrorMessage
        message={error}
        when="while getting the calculation"
        marginTop={5}
      />
    )
  }

  if (!result) return null

  // Object.entries(result.stations) is an array of station code & station response key value pairs
  const stationResults = Object.entries(result.stations).map(
    ([stationCode, stationResponse]) => {
      return (
        <GridItem key={stationCode}>
          <PercentileStationResultTable
            stationCode={stationCode}
            stationResponse={stationResponse}
          />
        </GridItem>
      )
    }
  )

  return (
    <div data-testid="percentile-result-tables" className={classes.root}>
      <GridContainer>{stationResults}</GridContainer>
      <GridContainer>
        <GridItem>
          <PercentileMeanResultTable meanValues={result.mean_values} />
        </GridItem>
      </GridContainer>
    </div>
  )
}
