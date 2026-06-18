import { act, fireEvent, render, screen } from '@testing-library/react'
import { createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import type { Mock } from 'vitest'
import * as layerDefinitions from '@/features/sfmsInsights/components/map/layerDefinitions'
import type { RasterError } from '@/features/sfmsInsights/components/map/layerManager'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import { createLayerMock, createTestStore } from '@/test/testUtils'

vi.mock('@wps/utils/vectorLayerUtils', async () => {
  return {
    getStyleJson: vi.fn(),
    createVectorTileLayer: vi.fn()
  }
})

type LoadingChangeFn = (isLoading: boolean, error?: RasterError) => void
const mockLayerManagerInstances: Array<{ onLoadingChange?: LoadingChangeFn; setMap: Mock; updateLayer: Mock }> = []

vi.mock('@/features/sfmsInsights/components/map/layerManager', () => ({
  LayerManager: class MockLayerManager {
    onLoadingChange: LoadingChangeFn | undefined
    setMap = vi.fn()
    updateLayer = vi.fn()
    constructor(options?: { onLoadingChange?: LoadingChangeFn; trackLoading?: boolean }) {
      this.onLoadingChange = options?.onLoadingChange
      mockLayerManagerInstances.push(this)
    }
  }
}))

vi.mock('@/features/sfmsInsights/components/map/layerDefinitions', async () => {
  const actual = await vi.importActual<typeof import('@/features/sfmsInsights/components/map/layerDefinitions')>(
    '@/features/sfmsInsights/components/map/layerDefinitions'
  )
  return {
    ...actual,
    getSnowPMTilesLayer: vi.fn(),
    getRasterLayer: vi.fn()
  }
})

describe('SFMSMap', () => {
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
  globalThis.ResizeObserver = ResizeObserver

  const mockSnowLayer = {
    ...createLayerMock('snowVector'),
    getZIndex: vi.fn(() => 53),
    getMinZoom: vi.fn(() => 4)
  }
  const mockFireWeatherLayer = createLayerMock('fwiRaster')

  const makeStore = (token = 'test-token') =>
    createTestStore({
      authentication: {
        isAuthenticated: true,
        error: null,
        token,
        authenticating: false,
        tokenRefreshed: false,
        idToken: undefined,
        idir: undefined,
        email: undefined,
        roles: []
      }
    })

  const renderWithStore = (component: React.ReactElement) =>
    render(<Provider store={makeStore()}>{component}</Provider>)

  beforeEach(() => {
    vi.clearAllMocks()
    mockLayerManagerInstances.length = 0
    ;(getStyleJson as Mock).mockResolvedValue({})
    ;(createVectorTileLayer as Mock).mockResolvedValue(createLayerMock('base'))
    ;(layerDefinitions.getSnowPMTilesLayer as Mock).mockReturnValue(mockSnowLayer)
    ;(layerDefinitions.getRasterLayer as Mock).mockReturnValue(mockFireWeatherLayer)
  })

  it('should render the map', () => {
    const { getByTestId } = renderWithStore(<SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />)
    const map = getByTestId('sfms-map')
    expect(map).toBeVisible()
  })

  it('should not add snow layer when snowDate is null', () => {
    renderWithStore(<SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />)
    expect(layerDefinitions.getSnowPMTilesLayer).not.toHaveBeenCalled()
  })

  it('should add snow layer when snowDate is provided and showSnow is true', () => {
    const snowDate = DateTime.fromISO('2025-11-02')
    renderWithStore(<SFMSMap snowDate={snowDate} rasterDate={DateTime.fromISO('2025-11-02')} showSnow={true} />)
    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenCalledWith(snowDate, 'test-token')
  })

  it('should not add snow layer when showSnow is false even if snowDate is provided', () => {
    const snowDate = DateTime.fromISO('2025-11-02')
    renderWithStore(<SFMSMap snowDate={snowDate} rasterDate={DateTime.fromISO('2025-11-02')} showSnow={false} />)
    expect(layerDefinitions.getSnowPMTilesLayer).not.toHaveBeenCalled()
  })

  it('should add snow layer by default when snowDate is provided and showSnow is not specified', () => {
    const snowDate = DateTime.fromISO('2025-11-02')
    renderWithStore(<SFMSMap snowDate={snowDate} rasterDate={DateTime.fromISO('2025-11-02')} />)
    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenCalledWith(snowDate, 'test-token')
  })

  it('should request new layer when raster date changes', () => {
    const store = makeStore()
    const { rerender } = render(
      <Provider store={store}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />
      </Provider>
    )

    rerender(
      <Provider store={store}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-03')} />
      </Provider>
    )

    expect(layerDefinitions.getRasterLayer).toHaveBeenLastCalledWith(
      DateTime.fromISO('2025-11-03'),
      'fwi',
      'test-token'
    )
  })

  it('should not request raster layer when rasterDate is null and rasterType is not fuel', () => {
    renderWithStore(<SFMSMap snowDate={null} rasterDate={null} rasterType="fwi" />)
    expect(layerDefinitions.getRasterLayer).not.toHaveBeenCalled()
  })

  it('should request raster layer for fuel type even when rasterDate is null', () => {
    renderWithStore(<SFMSMap snowDate={null} rasterDate={null} rasterType="fuel" />)
    expect(layerDefinitions.getRasterLayer).toHaveBeenCalledWith(null, 'fuel', 'test-token')
  })

  it('should request new layer when rasterType changes', () => {
    const store = makeStore()
    const { rerender } = render(
      <Provider store={store}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} rasterType="fwi" />
      </Provider>
    )

    rerender(
      <Provider store={store}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} rasterType="ffmc" />
      </Provider>
    )

    expect(layerDefinitions.getRasterLayer).toHaveBeenLastCalledWith(
      DateTime.fromISO('2025-11-02'),
      'ffmc',
      'test-token'
    )
  })

  it('should clear error when rasterDate changes', () => {
    const store = makeStore()
    const { rerender } = render(
      <Provider store={store}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />
      </Provider>
    )

    const error: RasterError = { type: 'not_found', message: 'Not found' }
    act(() => {
      getRasterOnLoadingChange()(false, error)
    })
    expect(screen.getByText(/not available for this date/i)).toBeInTheDocument()

    rerender(
      <Provider store={store}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-03')} />
      </Provider>
    )

    expect(screen.queryByText(/not available for this date/i)).not.toBeInTheDocument()
  })

  it('should clear error when rasterType changes', () => {
    const store = makeStore()
    const { rerender } = render(
      <Provider store={store}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} rasterType="fwi" />
      </Provider>
    )

    const error: RasterError = { type: 'not_found', message: 'Not found' }
    act(() => {
      getRasterOnLoadingChange()(false, error)
    })
    expect(screen.getByText(/not available for this date/i)).toBeInTheDocument()

    rerender(
      <Provider store={store}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} rasterType="ffmc" />
      </Provider>
    )

    expect(screen.queryByText(/not available for this date/i)).not.toBeInTheDocument()
  })

  it('should refresh raster layer when token changes', () => {
    const { rerender } = render(
      <Provider store={makeStore('old-token')}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />
      </Provider>
    )

    rerender(
      <Provider store={makeStore('new-token')}>
        <SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />
      </Provider>
    )

    expect(layerDefinitions.getRasterLayer).toHaveBeenLastCalledWith(DateTime.fromISO('2025-11-02'), 'fwi', 'new-token')
  })

  it('should update snow layer when snowDate changes', () => {
    const store = makeStore()
    const newSnowDate = DateTime.fromISO('2025-11-03')
    const { rerender } = render(
      <Provider store={store}>
        <SFMSMap snowDate={DateTime.fromISO('2025-11-02')} rasterDate={null} showSnow={true} />
      </Provider>
    )

    rerender(
      <Provider store={store}>
        <SFMSMap snowDate={newSnowDate} rasterDate={null} showSnow={true} />
      </Provider>
    )

    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenLastCalledWith(newSnowDate, 'test-token')
  })

  it('should refresh snow layer when token changes', () => {
    const snowDate = DateTime.fromISO('2025-11-02')
    const { rerender } = render(
      <Provider store={makeStore('old-token')}>
        <SFMSMap snowDate={snowDate} rasterDate={null} showSnow={true} />
      </Provider>
    )

    rerender(
      <Provider store={makeStore('new-token')}>
        <SFMSMap snowDate={snowDate} rasterDate={null} showSnow={true} />
      </Provider>
    )

    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenLastCalledWith(snowDate, 'new-token')
  })

  const getRasterOnLoadingChange = () => {
    // First LayerManager instance is the raster manager (trackLoading: true)
    return mockLayerManagerInstances[0].onLoadingChange!
  }

  it('should show loading indicator while raster layer is loading', () => {
    renderWithStore(<SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />)

    act(() => {
      getRasterOnLoadingChange()(true)
    })

    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('should show error notification when raster layer fails to load', () => {
    renderWithStore(<SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />)

    const error: RasterError = { type: 'not_found', message: 'Not found' }
    act(() => {
      getRasterOnLoadingChange()(false, error)
    })

    expect(screen.getByText(/not available for this date/i)).toBeInTheDocument()
  })

  it('should dismiss error notification when close button is clicked', async () => {
    renderWithStore(<SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />)

    const error: RasterError = { type: 'not_found', message: 'Not found' }
    act(() => {
      getRasterOnLoadingChange()(false, error)
    })
    expect(screen.getByText(/not available for this date/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /close/i }))

    expect(screen.queryByText(/not available for this date/i)).not.toBeInTheDocument()
  })

  it('should clear error notification when raster layer loads successfully', () => {
    renderWithStore(<SFMSMap snowDate={null} rasterDate={DateTime.fromISO('2025-11-02')} />)

    const error: RasterError = { type: 'not_found', message: 'Not found' }
    act(() => {
      getRasterOnLoadingChange()(false, error)
    })
    expect(screen.getByText(/not available for this date/i)).toBeInTheDocument()

    act(() => {
      getRasterOnLoadingChange()(false)
    })
    expect(screen.queryByText(/not available for this date/i)).not.toBeInTheDocument()
  })

  it('should re-add snow layer when showSnow changes from false to true', () => {
    const store = makeStore()
    const snowDate = DateTime.fromISO('2025-11-02')
    const { rerender } = render(
      <Provider store={store}>
        <SFMSMap snowDate={snowDate} rasterDate={null} showSnow={false} />
      </Provider>
    )
    expect(layerDefinitions.getSnowPMTilesLayer).not.toHaveBeenCalled()

    rerender(
      <Provider store={store}>
        <SFMSMap snowDate={snowDate} rasterDate={null} showSnow={true} />
      </Provider>
    )

    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenCalledWith(snowDate, 'test-token')
  })

  it('should remove snow layer when snowDate changes to null', () => {
    const store = makeStore()
    const { rerender } = render(
      <Provider store={store}>
        <SFMSMap snowDate={DateTime.fromISO('2025-11-02')} rasterDate={null} showSnow={true} />
      </Provider>
    )
    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenCalledTimes(1)

    rerender(
      <Provider store={store}>
        <SFMSMap snowDate={null} rasterDate={null} showSnow={true} />
      </Provider>
    )

    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenCalledTimes(1)
  })

  it('should not request snow layer when showSnow changes to false', () => {
    const store = makeStore()
    const snowDate = DateTime.fromISO('2025-11-02')
    const { rerender } = render(
      <Provider store={store}>
        <SFMSMap snowDate={snowDate} rasterDate={null} showSnow={true} />
      </Provider>
    )

    rerender(
      <Provider store={store}>
        <SFMSMap snowDate={snowDate} rasterDate={null} showSnow={false} />
      </Provider>
    )

    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenCalledTimes(1)
  })
})
