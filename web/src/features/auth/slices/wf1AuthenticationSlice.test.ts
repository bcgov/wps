import wf1AuthReducer, {
  initialState,
  authenticated,
  unAuthenticated,
  authenticateError
} from 'features/auth/slices/wf1AuthenticationSlice'

describe('wf1AuthenticationSlice', () => {
  const testToken = 'testToken'

  describe('reducer', () => {
    it('should be initialized with correct state', () => {
      expect(
        wf1AuthReducer(undefined, {
          type: undefined
        })
      ).toEqual(initialState)
    })
    it('should set authenticate start when authenticateStart is called', () => {
      expect(wf1AuthReducer(initialState, authenticated(testToken))).toEqual({
        ...initialState,
        wf1Token: testToken
      })
    })
    it('should unset token when unAuthenticated is dispatched ', () => {
      const signedInState = {
        ...initialState,
        wf1Token: testToken
      }

      expect(wf1AuthReducer(signedInState, unAuthenticated())).toEqual({
        ...initialState,
        wf1Token: undefined
      })
    })
    it('should unset token and set error when authenticateError is dispatched ', () => {
      const signedInState = {
        ...initialState,
        wf1Token: testToken
      }

      expect(wf1AuthReducer(signedInState, authenticateError('error'))).toEqual({
        ...initialState,
        wf1Token: undefined,
        error: 'error'
      })
    })
  })
})
