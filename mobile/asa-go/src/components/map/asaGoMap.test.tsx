import { act, render, screen, waitFor, within } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { RunType } from '@/api/fbaAPI'
import ASAGoMap, { type ASAGoMapProps } from '@/components/map/ASAGoMap'
import * as mapView from '@/components/map/mapView'
import * as featureStylers from '@/featureStylers'
import { initialState as dataInitialState } from '@/slices/dataSlice'
import { setDateOfInterest } from '@/slices/dateOfInterestSlice'
import { geolocationInitialState } from '@/slices/geolocationSlice'
import { createLayerMock, createTestStore, setupOpenLayersMocks } from '@/testUtils'
import { AdvisoryStatus } from '@/utils/constants'

vi.mock('@capacitor/filesystem', () => ({
  Filesystem: {
    readFile: vi.fn().mockResolvedValue({ data: JSON.stringify({}) }),
    writeFile: vi.fn().mockResolvedValue(undefined)
  },
  Directory: { Data: 'DATA' },
  Encoding: { UTF8: 'utf8' }
}))

setupOpenLayersMocks()
class ResizeObserver {
  observe() {
    // mock no-op
  }
  unobserve() {
    // mock no-op
  }
  disconnect() {
    // mock no-op
  }
}

vi.mock('@/layerDefinitions', async () => {
  const actual = await import('@/layerDefinitions')

  return {
    ...actual,
    createHFILayer: vi.fn().mockImplementation(() => Promise.resolve(createLayerMock('HFILayer'))),
    createBasemapLayer: vi.fn().mockImplementation(() => Promise.resolve(createLayerMock('vectorBasemapLayer')))
  }
})

import { createBasemapLayer, HFI_LAYER_NAME } from '@/layerDefinitions'

describe('ASAGoMap', () => {
  beforeAll(() => {
    globalThis.ResizeObserver = ResizeObserver
  })

  const defaultProps: ASAGoMapProps = {
    testId: 'asa-go-map',
    selectedFireShape: undefined,
    setSelectedFireShape: vi.fn(),
    setSelectedFireCentre: vi.fn(),
    setTab: vi.fn()
  }

  const mockPosition = {
    coords: {
      latitude: 49.2827,
      longitude: -123.1207,
      accuracy: 10,
      altitude: null,
      altitudeAccuracy: null,
      heading: null,
      speed: null
    },
    timestamp: Date.now()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the map', () => {
    const store = createTestStore()
    const { getByTestId } = render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    const mobileMap = getByTestId(defaultProps.testId)
    expect(mobileMap).toBeVisible()
  })

  it('renders the location button and location indicator', () => {
    const store = createTestStore({
      geolocation: {
        ...geolocationInitialState,
        position: mockPosition
      }
    })

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    const locationButton = screen.getByTestId('location-button')
    const locationIndicator = screen.getByTestId('user-location-indicator')
    expect(locationIndicator).toBeInTheDocument()
    expect(locationButton).toBeInTheDocument()
    expect(locationButton).not.toBeDisabled()
  })

  it('renders the layer switcher button and legend on click', async () => {
    const store = createTestStore()
    const { getByTestId } = render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    const legendButton = getByTestId('legend-toggle-button')
    expect(legendButton).toBeInTheDocument()

    await userEvent.click(legendButton)
    const legendPopover = getByTestId('asa-go-map-legend-popover')
    expect(legendPopover).toBeInTheDocument()
  })

  it('calls handleLayerVisibilityChange and updates layerVisibility state', async () => {
    const store = createTestStore()
    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    // Open legend popover
    const legendButton = screen.getByTestId('legend-toggle-button')
    await userEvent.click(legendButton)

    // Find a layer toggle (simulate Zone Status layer toggle)
    const zoneStatusToggle = screen.getByTestId('zone-checkbox')
    const zoneStatusCheckbox = within(zoneStatusToggle).getByRole('checkbox')
    expect(zoneStatusToggle).toBeInTheDocument()

    // Toggle off
    await userEvent.click(zoneStatusToggle)

    // The toggle should now be unchecked
    expect(zoneStatusCheckbox).not.toBeChecked()

    // Toggle on
    await userEvent.click(zoneStatusToggle)
    expect(zoneStatusCheckbox).toBeChecked()
  })

  it('calls setZoneStatusLayerVisibility for ZONE_STATUS_LAYER_NAME', async () => {
    const store = createTestStore()
    const setZoneStatusLayerVisibilityMock = vi.spyOn(
      await import('@/components/map/layerVisibility'),
      'setZoneStatusLayerVisibility'
    )

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    // Open legend popover
    const legendButton = screen.getByTestId('legend-toggle-button')
    await userEvent.click(legendButton)

    // Toggle Zone Status layer
    const zoneStatusToggle = screen.getByTestId('zone-checkbox')
    const zoneStatusCheckbox = within(zoneStatusToggle).getByRole('checkbox')
    await waitFor(() => expect(zoneStatusCheckbox).toBeChecked())
    await userEvent.click(zoneStatusToggle)

    expect(setZoneStatusLayerVisibilityMock).toHaveBeenCalled()
    expect(setZoneStatusLayerVisibilityMock).toHaveBeenCalledWith(
      expect.any(Object), // layer instance
      undefined, // no provincialSummary data
      false // visibility
    )
    await waitFor(() => expect(zoneStatusCheckbox).not.toBeChecked())

    await userEvent.click(zoneStatusToggle)
    expect(setZoneStatusLayerVisibilityMock).toHaveBeenCalledWith(
      expect.any(Object), // layer instance
      undefined, // no provincialSummary data
      true // visibility
    )
    await waitFor(() => expect(zoneStatusCheckbox).toBeChecked())
  })
  it('calls setDefaultLayerVisibility on the correct layer', async () => {
    const store = createTestStore()
    const setDefaultLayerVisibilityMock = vi.spyOn(
      await import('@/components/map/layerVisibility'),
      'setDefaultLayerVisibility'
    )

    const mockToggleLayersRef = {
      hfiVectorLayer: null
    }

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    // Open legend popover
    const legendButton = screen.getByTestId('legend-toggle-button')
    await userEvent.click(legendButton)

    // Toggle HFI layer
    const hfiToggle = screen.getByTestId('hfi-checkbox')
    // should be checked at first
    const hfiCheckbox = within(hfiToggle).getByRole('checkbox')
    await waitFor(() => expect(hfiCheckbox).toBeChecked())
    await userEvent.click(hfiToggle)

    // test that we're turning it off
    expect(setDefaultLayerVisibilityMock).toHaveBeenCalledWith(mockToggleLayersRef, HFI_LAYER_NAME, false)
    await waitFor(() => expect(hfiCheckbox).not.toBeChecked())
  })

  it('handles createBasemapLayer failure gracefully when offline', async () => {
    const error = new Error('Network unavailable')
    vi.mocked(createBasemapLayer).mockRejectedValueOnce(error)
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    const store = createTestStore()
    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    expect(screen.getByTestId(defaultProps.testId)).toBeVisible()

    await waitFor(() => {
      expect(warnSpy).toHaveBeenCalledWith(error)
    })

    warnSpy.mockRestore()
  })

  it('calls save and load map view state', async () => {
    const store = createTestStore({
      geolocation: {
        ...geolocationInitialState,
        position: mockPosition
      }
    })
    const loadMapViewStateMock = vi.spyOn(mapView, 'loadMapViewState')

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    expect(loadMapViewStateMock).toHaveBeenCalled()
  })

  it('styles zones using provincial summary data for the store date of interest, and re-styles when the date changes to one with no data', async () => {
    const fireShapeStylerSpy = vi.spyOn(featureStylers, 'fireShapeStyler')
    const store = createTestStore({
      dateOfInterest: { dateKey: '2025-08-01' },
      data: {
        ...dataInitialState,
        provincialSummaries: {
          '2025-08-01': {
            runParameter: { for_date: '2025-08-01', run_datetime: '2025-08-01T00:00:00Z', run_type: RunType.FORECAST },
            data: [
              {
                fire_shape_id: 1,
                fire_shape_name: 'Zone-1',
                fire_centre_name: 'Test Fire Centre',
                status: AdvisoryStatus.WARNING
              }
            ]
          }
        }
      }
    })

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    await waitFor(() => {
      expect(fireShapeStylerSpy).toHaveBeenCalledWith(
        expect.arrayContaining([expect.objectContaining({ fire_shape_id: 1, status: AdvisoryStatus.WARNING })]),
        expect.any(Boolean)
      )
    })

    fireShapeStylerSpy.mockClear()

    act(() => {
      store.dispatch(setDateOfInterest('2025-08-02'))
    })

    await waitFor(() => {
      expect(fireShapeStylerSpy).toHaveBeenCalledWith(undefined, expect.any(Boolean))
    })
  })
})
