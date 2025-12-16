import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import { createLayerMock, createTestStore } from '@/test/testUtils'
import { createVectorTileLayer, getStyleJson } from '@/utils/vectorLayerUtils'
import { render } from '@testing-library/react'
import { DateTime } from 'luxon'
import { Mock } from 'vitest'
import * as layerDefinitions from '@/features/sfmsInsights/components/map/layerDefinitions'
import { Provider } from 'react-redux'

vi.mock('@/utils/vectorLayerUtils', async () => {
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
    getFireWeatherRasterLayer: vi.fn()
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
  window.ResizeObserver = ResizeObserver

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
    ;(layerDefinitions.getFireWeatherRasterLayer as Mock).mockReturnValue(mockFireWeatherLayer)
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
    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenCalledWith(snowDate)
  })

  it('should not add snow layer when showSnow is false even if snowDate is provided', () => {
    const snowDate = DateTime.fromISO('2025-11-02')
    renderWithStore(<SFMSMap snowDate={snowDate} rasterDate={DateTime.fromISO('2025-11-02')} showSnow={false} />)
    expect(layerDefinitions.getSnowPMTilesLayer).not.toHaveBeenCalled()
  })

  it('should add snow layer by default when snowDate is provided and showSnow is not specified', () => {
    const snowDate = DateTime.fromISO('2025-11-02')
    renderWithStore(<SFMSMap snowDate={snowDate} rasterDate={DateTime.fromISO('2025-11-02')} />)
    expect(layerDefinitions.getSnowPMTilesLayer).toHaveBeenCalledWith(snowDate)
  })
})
