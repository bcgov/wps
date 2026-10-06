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
    createBasemapLayer: vi.fn().mockImplementation(() => Promise.resolve(createLayerMock('vectorBasemapLayer'))),
    createLocalBasemapVectorLayer: vi
      .fn()
      .mockImplementation(() => Promise.resolve(createLayerMock('localBasemapLayer')))
  }
})

import { createBasemapLayer, createHFILayer, createLocalBasemapVectorLayer, HFI_LAYER_NAME } from '@/layerDefinitions'
import { PMTilesFileVectorSource } from '@/utils/pmtilesVectorSource'

const createPMTilesSource = (state: 'ready' | 'error') => {
  const source = new PMTilesFileVectorSource({})
  source.setState(state)
  return source
}

describe('ASAGoMap', () => {
  beforeAll(() => {
    globalThis.ResizeObserver = ResizeObserver
  })

  const defaultProps: ASAGoMapProps = {
    testId: 'asa-go-map',
    operationalDataLoading: false,
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
      speed: null,
      magneticHeading: null,
      trueHeading: null,
      headingAccuracy: null,
      course: null
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

  it('reports layer setup loading until initial layers settle', async () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    const map = screen.getByTestId(defaultProps.testId)
    expect(map).toHaveAttribute('aria-busy', 'true')
    await waitFor(() => expect(map).toHaveAttribute('aria-busy', 'false'))
  })

  it('reports operational data loading after layer setup settles', async () => {
    const store = createTestStore()
    const { rerender } = render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )
    const map = screen.getByTestId(defaultProps.testId)
    await waitFor(() => expect(map).toHaveAttribute('aria-busy', 'false'))

    rerender(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} operationalDataLoading />
      </Provider>
    )

    expect(map).toHaveAttribute('aria-busy', 'true')
  })

  it('stays loading until overlapping layer loads settle', async () => {
    let resolveBasemap: (layer: ReturnType<typeof createLayerMock>) => void = () => {}
    let resolveHFI: (layer: ReturnType<typeof createLayerMock>) => void = () => {}
    const basemapPromise = new Promise<ReturnType<typeof createLayerMock>>(resolve => {
      resolveBasemap = resolve
    })
    const hfiPromise = new Promise<ReturnType<typeof createLayerMock>>(resolve => {
      resolveHFI = resolve
    })
    vi.mocked(createBasemapLayer).mockReturnValueOnce(basemapPromise as never)
    vi.mocked(createHFILayer).mockReturnValueOnce(hfiPromise as never)
    const staticLayerSpy = vi
      .spyOn(PMTilesFileVectorSource, 'createStaticLayer')
      .mockResolvedValue(createPMTilesSource('ready'))
    const dateKey = '2025-08-01'
    const store = createTestStore({
      dateOfInterest: { dateKey },
      runParameters: {
        loading: false,
        error: null,
        runParameters: {
          [dateKey]: {
            for_date: dateKey,
            run_datetime: '2025-08-01T00:00:00Z',
            run_type: RunType.FORECAST
          }
        }
      }
    })

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )
    const map = screen.getByTestId(defaultProps.testId)
    await waitFor(() => {
      expect(createBasemapLayer).toHaveBeenCalled()
      expect(createHFILayer).toHaveBeenCalled()
    })

    await act(async () => resolveHFI(createLayerMock('HFILayer')))
    expect(map).toHaveAttribute('aria-busy', 'true')

    await act(async () => resolveBasemap(createLayerMock('vectorBasemapLayer')))
    await waitFor(() => expect(map).toHaveAttribute('aria-busy', 'false'))

    staticLayerSpy.mockRestore()
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

  it('settles layer loading when the online basemap is unavailable', async () => {
    vi.mocked(createBasemapLayer).mockRejectedValueOnce(new Error('Network unavailable'))
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const staticLayerSpy = vi
      .spyOn(PMTilesFileVectorSource, 'createStaticLayer')
      .mockResolvedValue(createPMTilesSource('ready'))

    const store = createTestStore()
    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    expect(screen.getByTestId(defaultProps.testId)).toBeVisible()

    await waitFor(() => {
      expect(createBasemapLayer).toHaveBeenCalled()
      expect(screen.getByTestId(defaultProps.testId)).toHaveAttribute('aria-busy', 'false')
    })

    staticLayerSpy.mockRestore()
    warnSpy.mockRestore()
  })

  it('settles layer loading when neither basemap is available', async () => {
    vi.mocked(createBasemapLayer).mockRejectedValueOnce(new Error('Online basemap unavailable'))
    const failedLocalBasemap = createLayerMock('localBasemapLayer')
    failedLocalBasemap.getSource.mockReturnValue({ getState: vi.fn(() => 'error') })
    vi.mocked(createLocalBasemapVectorLayer).mockResolvedValueOnce(failedLocalBasemap as never)
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const staticLayerSpy = vi
      .spyOn(PMTilesFileVectorSource, 'createStaticLayer')
      .mockResolvedValue(createPMTilesSource('ready'))
    const store = createTestStore()

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    await waitFor(() => expect(screen.getByTestId(defaultProps.testId)).toHaveAttribute('aria-busy', 'false'))

    staticLayerSpy.mockRestore()
    warnSpy.mockRestore()
  })

  it('settles layer loading when static PMTiles sources fail', async () => {
    const staticLayerSpy = vi
      .spyOn(PMTilesFileVectorSource, 'createStaticLayer')
      .mockResolvedValue(createPMTilesSource('error'))
    const store = createTestStore()

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    await waitFor(() => expect(screen.getByTestId(defaultProps.testId)).toHaveAttribute('aria-busy', 'false'))

    staticLayerSpy.mockRestore()
  })

  it('settles layer loading when the HFI source fails', async () => {
    const failedHFILayer = createLayerMock('HFILayer')
    failedHFILayer.getSource.mockReturnValue({ getState: vi.fn(() => 'error') })
    vi.mocked(createHFILayer).mockResolvedValueOnce(failedHFILayer as never)
    const staticLayerSpy = vi
      .spyOn(PMTilesFileVectorSource, 'createStaticLayer')
      .mockResolvedValue(createPMTilesSource('ready'))
    const dateKey = '2025-08-01'
    const store = createTestStore({
      dateOfInterest: { dateKey },
      runParameters: {
        loading: false,
        error: null,
        runParameters: {
          [dateKey]: {
            for_date: dateKey,
            run_datetime: '2025-08-01T00:00:00Z',
            run_type: RunType.FORECAST
          }
        }
      }
    })

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    )

    await waitFor(() => expect(screen.getByTestId(defaultProps.testId)).toHaveAttribute('aria-busy', 'false'))

    staticLayerSpy.mockRestore()
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
