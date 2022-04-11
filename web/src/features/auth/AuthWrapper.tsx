import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { authenticate, testAuthenticate } from 'features/auth/slices/authenticationSlice'
import axios from 'api/axios'
import { AppThunk } from 'app/store'
import { selectToken, selectAuthentication } from 'app/rootReducer'
import { TEST_AUTH } from 'utils/env'

interface Props {
  shouldAuthenticate: boolean
  children: React.ReactElement
}

// Used for test authentication
const testToken =
  'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJQZUlFYlpQUm5xaTk2ZDl6RFJZT3B5RFBqVHdkei1tcF9kRHJPYmJ4Uko0In0.eyJleHAiOjE2NDk0NTYyMDksImlhdCI6MTY0OTQ1NDQwOSwiYXV0aF90aW1lIjoxNjQ5NDQ3Njg4LCJqdGkiOiI5OGMxZDM1ZC1lYWU4LTQzNTItOWE0Yy04ZTk3ZWY4NTJmMWUiLCJpc3MiOiJodHRwczovL2Rldi5vaWRjLmdvdi5iYy5jYS9hdXRoL3JlYWxtcy84d2w2eDRjcCIsInN1YiI6ImQ4MWI3MTkwLTUzMmItNDNhYi05Y2ZmLWZlOThjMGJlNjNhZSIsInR5cCI6IkJlYXJlciIsImF6cCI6Indwcy13ZWIiLCJub25jZSI6IjIxMWM3NjgzLTQ2M2EtNDMwNC04NThlLWNmYjA0MzA0MjhlMSIsInNlc3Npb25fc3RhdGUiOiIwMGJmNTQ0Mi0yNjliLTQ5MTYtOTAyOS1iMTllMmUyNDM0MmUiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbIioiXSwicmVzb3VyY2VfYWNjZXNzIjp7Indwcy13ZWIiOnsicm9sZXMiOlsiaGZpX3NlbGVjdF9zdGF0aW9uIiwidGVzdC1yb2xlIiwiaGZpX3NldF9maXJlX3N0YXJ0cyJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsIm5hbWUiOiJDb25vciBCcmFkeSIsInByZWZlcnJlZF91c2VybmFtZSI6ImNicmFkeUBpZGlyIiwiZ2l2ZW5fbmFtZSI6IkNvbm9yIiwiZmFtaWx5X25hbWUiOiJCcmFkeSIsImVtYWlsIjoiY29ub3IuYnJhZHlAZ292LmJjLmNhIn0.gmJyQqjqtmxwj-eD57cN2_om_5J8GsDlCyeFcEueTMtc_JhKxJDgH90LVUQ0HizdZObpid61cjUJnogb6gyPrzJgesb2FEZaMd88ACU9akbHvYhe4TrBjDPGev5XE9SdMpag8vbVsNa4JIUn6KQxUDhJw8a_olTsqunTT5KKdrPSQyCExk6nDFGE2lZqgDUDIszbpLkzv7xV9T9MOoWeVDJSQvfw3aH4ZXUZ26rxt4RQGDJTInHO6M91zwWPc6Gi0KPxMNv7DG7eyJ8FWg1e8WeptZ6gdcKFgGEIY8lih2TdmeP40gzti1KpBXbMVwLavlXbS46wHgXQTbm-2CW6mQ'

const setAxiosRequestInterceptors = (): AppThunk => (_, getState) => {
  // Use axios interceptors to intercept any requests and add authorization headers.
  axios.interceptors.request.use(config => {
    const token = selectToken(getState())
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  })
}

const AuthWrapper = ({ children }: Props) => {
  const dispatch = useDispatch()
  const { isAuthenticated, authenticating, error } = useSelector(selectAuthentication)
  const shouldAuthenticate =
    process.env.NODE_ENV === 'production' || window.Cypress === undefined

  useEffect(() => {
    if (TEST_AUTH || window.Cypress) {
      dispatch(testAuthenticate(true, testToken))
    } else if (shouldAuthenticate) {
      dispatch(authenticate())
      dispatch(setAxiosRequestInterceptors())
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (!shouldAuthenticate) {
    return children
  }

  if (error) {
    return <div>{error}</div>
  }

  if (authenticating) {
    return <div>Signing in...</div>
  }

  if (!isAuthenticated) {
    return <div>You are not authenticated!</div>
  }

  return children
}

export default React.memo(AuthWrapper)
