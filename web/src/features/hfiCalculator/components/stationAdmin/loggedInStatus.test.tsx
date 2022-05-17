import { render } from '@testing-library/react'
import LoggedInStatus from 'features/hfiCalculator/components/stationAdmin/LoggedInStatus'
import React from 'react'

describe('LoggedInStatus', () => {
  const idir = 'test@idir'
  it('should render nothing if not authenticated', () => {
    const { container } = render(<LoggedInStatus isAuthenticated={false} roles={[]} idir={undefined} />)
    expect(container).toBeEmptyDOMElement()
  })
  it('should render locked lock and idir username if authenticated without any role', () => {
    const { getByTestId, container } = render(<LoggedInStatus isAuthenticated={true} roles={[]} idir={idir} />)
    const loggedInIcon = getByTestId('LockOutlinedIcon')
    expect(loggedInIcon).toBeDefined()

    expect(container).toHaveTextContent(idir)
    expect(container).toHaveTextContent('Read only')
  })
  it('should render unlocked lock and idir username if authenticated with any role(s)', () => {
    const { getByTestId, container } = render(
      <LoggedInStatus isAuthenticated={true} roles={['test-role']} idir={idir} />
    )
    const loggedInIcon = getByTestId('LockOpenOutlinedIcon')
    expect(loggedInIcon).toBeDefined()

    expect(container).toHaveTextContent(idir)
    expect(container).toHaveTextContent('Editing')
  })
})
