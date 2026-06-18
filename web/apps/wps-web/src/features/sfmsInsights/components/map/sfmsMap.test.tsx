import { render } from '@testing-library/react'
import { createVectorTileLayer, getStyleJson } from '@wps/utils/vectorLayerUtils'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import type { Mock } from 'vitest'
import * as layerDefinitions from '@/features/sfmsInsights/components/map/layerDefinitions'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import { createLayerMock, createTestStore } from '@/test/testUtils'

vi.mock('@wps/utils/vectorLayerUtils', async () => {
  return {
    getStyleJson: vi.fn(),
    createVectorTileLayer: vi.fn()
  }
})

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

  const renderWithStore = (component: React.ReactElement) => {
    const store = createTestStore({
      authentication: {
        isAuthenticated: true,
        error: null,
        token: 'test-token',
        authenticating: false,
        tokenRefreshed: false,
        idToken: undefined,
        idir: undefined,
        email: undefined,
        roles: []
      }
    })
    return render(<Provider store={store}>{component}</Provider>)
  }

  beforeEach(() => {
    vi.clearAllMocks()
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
    const store = createTestStore({
      authentication: {
        isAuthenticated: true,
        error: null,
        token: 'test-token',
        authenticating: false,
        tokenRefreshed: false,
        idToken: undefined,
        idir: undefined,
        email: undefined,
        roles: []
      }
    })
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
    const store = createTestStore({
      authentication: {
        isAuthenticated: true,
        error: null,
        token: 'test-token',
        authenticating: false,
        tokenRefreshed: false,
        idToken: undefined,
        idir: undefined,
        email: undefined,
        roles: []
      }
    })
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

  it('should update snow layer when snowDate changes', () => {
    const store = createTestStore({
      authentication: {
        isAuthenticated: true,
        error: null,
        token: 'test-token',
        authenticating: false,
        tokenRefreshed: false,
        idToken: undefined,
        idir: undefined,
        email: undefined,
        roles: []
      }
    })
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

  it('should not request snow layer when showSnow changes to false', () => {
    const store = createTestStore({
      authentication: {
        isAuthenticated: true,
        error: null,
        token: 'test-token',
        authenticating: false,
        tokenRefreshed: false,
        idToken: undefined,
        idir: undefined,
        email: undefined,
        roles: []
      }
    })
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
