/* eslint-disable @typescript-eslint/no-explicit-any */
import authReducer, {
  decodeRoles,
  initialState,
  authenticateStart,
  authenticateFinished,
  authenticateError,
  refreshTokenFinished,
  signoutFinished,
  signoutError,
  decodeUserDetails
} from 'features/auth/slices/authenticationSlice'
import sinon from 'sinon'
import * as jwt from 'jwt-decode'
import { ROLES } from 'features/auth/roles'

describe('authenticationSlice', () => {
  let sandbox: sinon.SinonSandbox
  beforeEach(() => {
    sandbox = sinon.createSandbox()
  })
  afterEach(() => {
    sandbox.restore()
  })
  const testToken = 'testToken'
  const idir_username = 'test@idir'
  const email = 'test@example.com'
  const decodedAllRoles = {
    idir_username,
    email,
    client_roles: Object.values(ROLES.HFI)
  }
  const decodedNoRoles = {
    idir_username,
    email,
    client_roles: []
  }
  it('should return all roles of a user from a token', () => {
    sandbox.stub(jwt, 'jwtDecode').returns(decodedAllRoles)
    const roles = decodeRoles(testToken)
    expect(roles).toEqual(Object.values(ROLES.HFI))
  })
  it('should return no roles if user token has none defined', () => {
    sandbox.stub(jwt, 'jwtDecode').returns(decodedNoRoles)
    const roles = decodeRoles(testToken)
    expect(roles).toEqual([])
  })
  it('should return idir username from token', () => {
    sandbox.stub(jwt, 'jwtDecode').returns(decodedNoRoles)
    const userDetails = decodeUserDetails(testToken)
    expect(userDetails).toEqual({ idir: idir_username, email })
  })
  describe('reducer', () => {
    it('should be initialized with correct state', () => {
      expect(
        authReducer(undefined, {
          type: undefined
        })
      ).toEqual(initialState)
    })
    it('should set authenticate start when authenticateStart is called', () => {
      expect(authReducer(initialState, authenticateStart())).toEqual({
        ...initialState,
        authenticating: true
      })
    })
    it('should set token with roles correctly when authentication finishes', () => {
      sandbox.stub(jwt, 'jwtDecode').returns(decodedAllRoles)
      expect(
        authReducer(initialState, authenticateFinished({ isAuthenticated: true, token: testToken, idToken: testToken }))
      ).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: true,
        idir: 'test@idir',
        email,
        token: testToken,
        idToken: testToken,
        roles: Object.values(ROLES.HFI)
      })
    })
    it('should set token without roles correctly when authentication finishes', () => {
      sandbox.stub(jwt, 'jwtDecode').returns(decodedNoRoles)
      expect(
        authReducer(initialState, authenticateFinished({ isAuthenticated: true, token: testToken, idToken: testToken }))
      ).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: true,
        idir: 'test@idir',
        email,
        token: testToken,
        idToken: testToken,
        roles: []
      })
    })
    it('should set error state when authentication fails', () => {
      const error = 'an error occurred'
      expect(authReducer(initialState, authenticateError(error))).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: false,
        error,
        roles: []
      })
    })
    it('should set state correctly when token refreshes with roles', () => {
      sandbox.stub(jwt, 'jwtDecode').returns(decodedAllRoles)
      expect(
        authReducer(initialState, refreshTokenFinished({ tokenRefreshed: true, token: testToken, idToken: testToken }))
      ).toEqual({
        ...initialState,
        authenticating: false,
        tokenRefreshed: true,
        token: testToken,
        idToken: testToken,
        idir: 'test@idir',
        email,
        roles: Object.values(ROLES.HFI)
      })
    })
    it('should set state correctly when token refreshes without roles', () => {
      sandbox.stub(jwt, 'jwtDecode').returns(decodedNoRoles)
      expect(
        authReducer(initialState, refreshTokenFinished({ tokenRefreshed: true, token: testToken, idToken: testToken }))
      ).toEqual({
        ...initialState,
        authenticating: false,
        tokenRefreshed: true,
        token: testToken,
        idToken: testToken,
        idir: 'test@idir',
        email,
        roles: []
      })
    })
    describe('signout', () => {
      it('should unset isAuthenticated, roles and token states when signout is dispatched ', () => {
        sandbox.stub(jwt, 'jwtDecode').returns(decodedAllRoles)
        const signedInState = {
          authenticating: false,
          isAuthenticated: true,
          tokenRefreshed: false,
          token: testToken,
          idToken: testToken,
          idir: 'test@idir',
          email,
          roles: Object.values(ROLES.HFI),
          error: null
        }

        expect(authReducer(signedInState, signoutFinished())).toEqual({
          ...signedInState,
          authenticating: false,
          isAuthenticated: false,
          token: undefined,
          idToken: undefined,
          roles: []
        })
      })
      it('should unset isAuthenticated, roles, token and set error states when signout is dispatched and fails ', () => {
        sandbox.stub(jwt, 'jwtDecode').returns(decodedAllRoles)
        const signedInState = {
          authenticating: false,
          isAuthenticated: true,
          tokenRefreshed: false,
          token: testToken,
          idToken: testToken,
          idir: 'test@idir',
          email,
          roles: Object.values(ROLES.HFI),
          error: null
        }
        const error = 'error'

        expect(authReducer(signedInState, signoutError(error))).toEqual({
          ...signedInState,
          authenticating: false,
          isAuthenticated: false,
          token: undefined,
          idToken: undefined,
          roles: [],
          error: error
        })
      })
    })
  })
})
