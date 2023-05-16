import { render } from '@testing-library/react'
import store from 'app/store'
import MoreCast2AuthWrapper from 'features/auth/components/MoreCast2AuthWrapper'
import { Provider } from 'react-redux'
import React from 'react'
import { WF1_AUTH_URL } from 'utils/env'

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

  it('should make auth request to wf1 when not authd', () => {
    expect(window.location.href).toBe('')

    render(
      <Provider store={store}>
        <MoreCast2AuthWrapper>
          <div></div>
        </MoreCast2AuthWrapper>
      </Provider>
    )
    expect(window.location.href).toBe(WF1_AUTH_URL)
  })

  it('should not make auth request to wf1 when already authd', () => {
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
      <Provider store={store}>
        <MoreCast2AuthWrapper>
          <div></div>
        </MoreCast2AuthWrapper>
      </Provider>
    )
    expect(window.location.href).toBe(authedUrl)
  })
})
