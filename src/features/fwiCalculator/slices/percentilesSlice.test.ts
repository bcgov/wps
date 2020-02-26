import reducer, {
  percentileInitialState,
  getPercentilesSuccess
} from 'features/fwiCalculator/slices/percentilesSlice'
import { PercentilesResponse } from 'api/percentileAPI'

describe('Percentiles Slice', () => {
  it('Should return initial state on first run', () => {
    const result = reducer(undefined, { type: 'someAction' })
    expect(result).toEqual(percentileInitialState)
  })

  it('Should return new state after fetching the result', () => {
    const data: PercentilesResponse = {
      stations: {},
      mean_values: {
        FFMC: 1,
        BUI: 1,
        ISI: 1
      },
      percentile: 90,
      year_range: { start: 2010, end: 2019 }
    }
    const nextState = reducer(
      percentileInitialState,
      getPercentilesSuccess(data)
    )
    expect(nextState).not.toBe(percentileInitialState)
    expect(nextState.result).toBe(data)
  })
})
