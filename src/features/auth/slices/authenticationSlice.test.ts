import reducer, {
  initialState,
  authenticationFinished
} from 'features/auth/slices/authenticationSlice'

describe('Authentication Slice', () => {
  it('Should return initial state on first run', () => {
    const result = reducer(undefined, { type: 'someAction' })
    expect(result).toEqual(initialState)
  })

  it('Should return new state after authentication is finished', () => {
    const nextState = reducer(initialState, authenticationFinished(true))
    expect(nextState).not.toBe(initialState) // check referential identity
    expect(nextState.isAuthenticated).toBe(true)
  })
})
