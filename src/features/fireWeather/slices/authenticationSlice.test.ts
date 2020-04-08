import reducer, {
  authenticationInitialState,
  getAuthenticationSuccess
} from 'features/fireWeather/slices/authenticationSlice'

describe('Authentication Slice', () => {
  it('Should return initial state on first run', () => {
    const result = reducer(undefined, { type: 'someAction' })
    expect(result).toEqual(authenticationInitialState)
  })

  it('Should return new state after fetching authentication', () => {
    const nextState = reducer(
      authenticationInitialState,
      getAuthenticationSuccess(true)
    )
    expect(nextState).not.toBe(authenticationInitialState) // check referential identity
    expect(nextState.isAuthenticated).toBe(true)
  })
})
