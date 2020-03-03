import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { useSelector } from 'react-redux'

import { selectPercentilesReducer } from 'app/rootReducer'
import { PercentileMeanResultTable } from 'features/fwiCalculator/components/PercentileMeanResultTable'
import { PercentileStationResultTable } from 'features/fwiCalculator/components/PercentileStationResultTable'
import { ErrorMessage } from 'components/ErrorMessage'

const useStyles = makeStyles({
  stations: {
    display: 'flex'
  },
  error: {
    marginTop: 5
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
        <PercentileStationResultTable
          key={stationCode}
          stationCode={stationCode}
          stationResponse={stationResponse}
        />
      )
    }
  )

  return (
    <div data-testid="percentile-result-tables">
      <div className={classes.stations}>{stationResults}</div>
      <PercentileMeanResultTable meanValues={result.mean_values} />
    </div>
  )
}
