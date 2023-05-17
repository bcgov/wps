import { render } from '@testing-library/react'
import MoreCast2AuthWrapper from 'features/auth/components/MoreCast2AuthWrapper'
import { Provider } from 'react-redux'
import authReducer, { initialState, AuthState } from 'features/auth/slices/authenticationSlice'
import wf1AuthReducer from 'features/auth/slices/wf1AuthenticationSlice'
import React from 'react'
import { WF1_AUTH_URL } from 'utils/env'
import { ROLES } from 'features/auth/roles'
import { combineReducers, configureStore } from '@reduxjs/toolkit'

describe('MoreCast2AuthWrapper', () => {
  const { location } = window

  beforeEach((): void => {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    delete window.location
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    window.location = {
      href: ''
    }
  })

  afterEach((): void => {
    window.location = location
  })

  const buildTestStore = (initialState: AuthState) => {
    const rootReducer = combineReducers({ authentication: authReducer, wf1Authentication: wf1AuthReducer })
    const testStore = configureStore({
      reducer: rootReducer,
      preloadedState: {
        authentication: initialState
      }
    })
    return testStore
  }

  it('should make auth request to wf1 if forecaster when not authd', () => {
    const testStore = buildTestStore({
      ...initialState,
      roles: [ROLES.MORECAST_2.WRITE_FORECAST]
    })

    expect(window.location.href).toBe('')

    render(
      <Provider store={testStore}>
        <MoreCast2AuthWrapper>
          <div></div>
        </MoreCast2AuthWrapper>
      </Provider>
    )
    expect(window.location.href).toBe(WF1_AUTH_URL)
  })

  it('should not make auth request to wf1 if forecaster when already authd', () => {
    const testStore = buildTestStore({
      ...initialState,
      roles: [ROLES.MORECAST_2.WRITE_FORECAST]
    })
    const authedUrl = 'test.com/#access_token=t&'
    expect(window.location.href).toBe('')
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    delete window.location
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    window.location = {
      href: authedUrl
    }

    render(
      <Provider store={testStore}>
        <MoreCast2AuthWrapper>
          <div></div>
        </MoreCast2AuthWrapper>
      </Provider>
    )
    expect(window.location.href).toBe(authedUrl)
  })

  it('should not make auth request to wf1 if not a forecaster', () => {
    const testStore = buildTestStore({
      ...initialState,
      roles: []
    })
    expect(window.location.href).toBe('')

    render(
      <Provider store={testStore}>
        <MoreCast2AuthWrapper>
          <div></div>
        </MoreCast2AuthWrapper>
      </Provider>
    )
    expect(window.location.href).toBe('')
  })
})
