/* eslint-disable no-undef */
import reducer, {
  stationsInitialState,
  getStationsSuccess
} from 'features/fwiCalculator/slices/stationsSlice'

describe('Stations Slice', () => {
  it('Should return initial state on first run', () => {
    const result = reducer(undefined, { type: '' })
    expect(result).toEqual(stationsInitialState)
  })

  it('Should return new state after fetching stations', () => {
    const data = [
      {
        code: 331,
        name: 'ASHNOLA'
      },
      {
        code: 334,
        name: 'MCCUDDY'
      },
      {
        code: 328,
        name: 'PENTICTON RS'
      }
    ]
    const nextState = reducer(stationsInitialState, getStationsSuccess(data))
    expect(nextState).not.toBe(stationsInitialState) // check referential identity
    expect(nextState.stations).toBe(data)
  })
})
