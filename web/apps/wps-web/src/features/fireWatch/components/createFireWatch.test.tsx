import { render, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import CreateFireWatch from '@/features/fireWatch/components/CreateFireWatch'
import { createTestStore } from '@/test/testUtils'

vi.mock('@wps/api/stationAPI', () => ({
  getStations: vi.fn(() => Promise.resolve([])),
  StationSource: { wildfire_one: 'wildfire_one', unspecified: 'unspecified' }
}))

vi.mock('@wps/api/psuAPI', () => ({
  getFireCentres: vi.fn(() => Promise.resolve({ fire_centres: [] }))
}))

describe('CreateFireWatch', () => {
  let testStore: ReturnType<typeof createTestStore>

  beforeEach(() => {
    testStore = createTestStore()
  })

  const renderCreateFireWatch = () =>
    render(
      <Provider store={testStore}>
        <CreateFireWatch />
      </Provider>
    )

  it('dispatches fetchWxStations and fetchFireWatchFireCentres on mount', async () => {
    const dispatchSpy = vi.spyOn(testStore, 'dispatch')
    renderCreateFireWatch()

    await waitFor(() => {
      expect(dispatchSpy).toHaveBeenCalled()
    })
  })

  it('renders the stepper with all steps', () => {
    const { getByText } = renderCreateFireWatch()

    expect(getByText('Info')).toBeInTheDocument()
    expect(getByText('Location')).toBeInTheDocument()
    expect(getByText('Weather')).toBeInTheDocument()
    expect(getByText('Fuel Info')).toBeInTheDocument()
    expect(getByText('FBP Indices')).toBeInTheDocument()
    expect(getByText('Submit')).toBeInTheDocument()
  })
})
