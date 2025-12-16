import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { SFMSInsightsPage } from './SFMSInsightsPage'
import { Provider } from 'react-redux'
import { createTestStore } from '@/test/testUtils'
import { getMostRecentProcessedSnowByDate } from '@/api/snow'
import { DateTime } from 'luxon'
import { Mock } from 'vitest'

vi.mock('@/api/snow', () => ({
  getMostRecentProcessedSnowByDate: vi.fn()
}))

vi.mock('@/features/sfmsInsights/components/map/SFMSMap', () => {
  return {
    default: ({ showSnow }: { showSnow: boolean }) => (
      <div data-testid="sfms-map" data-show-snow={showSnow}>
        Mock SFMS Map
      </div>
    )
  }
})

vi.mock('@/utils/vectorLayerUtils', () => ({
  getStyleJson: vi.fn(),
  createVectorTileLayer: vi.fn()
}))

vi.mock('@/features/landingPage/components/Footer', () => ({
  default: () => <div data-testid="footer">Mock Footer</div>
}))

vi.mock('@/components/GeneralHeader', () => ({
  GeneralHeader: () => <div data-testid="general-header">Mock Header</div>
}))

describe('SFMSInsightsPage', () => {
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
    ;(getMostRecentProcessedSnowByDate as Mock).mockResolvedValue({
      forDate: DateTime.fromISO('2025-11-02'),
      processedDate: DateTime.fromISO('2025-11-02'),
      snowSource: 'viirs'
    })
  })

  it('should render the snow checkbox', async () => {
    renderWithStore(<SFMSInsightsPage />)
    await waitFor(() => {
      const checkbox = screen.getByRole('checkbox', { name: /show snow/i })
      expect(checkbox).toBeInTheDocument()
    })
  })

  it('should have the snow checkbox checked by default', async () => {
    renderWithStore(<SFMSInsightsPage />)
    await waitFor(() => {
      const checkbox = screen.getByRole('checkbox', { name: /show snow/i }) as HTMLInputElement
      expect(checkbox.checked).toBe(true)
    })
  })

  it('should toggle snow checkbox when clicked', async () => {
    renderWithStore(<SFMSInsightsPage />)

    await waitFor(() => {
      const checkbox = screen.getByRole('checkbox', { name: /show snow/i })
      expect(checkbox).toBeInTheDocument()
    })

    const checkbox = screen.getByRole('checkbox', { name: /show snow/i }) as HTMLInputElement
    expect(checkbox.checked).toBe(true)

    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(false)

    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(true)
  })

  it('should pass showSnow prop to SFMSMap when checkbox is checked', async () => {
    renderWithStore(<SFMSInsightsPage />)

    await waitFor(() => {
      const map = screen.getByTestId('sfms-map')
      expect(map).toHaveAttribute('data-show-snow', 'true')
    })
  })

  it('should pass showSnow=false to SFMSMap when checkbox is unchecked', async () => {
    renderWithStore(<SFMSInsightsPage />)
    const checkbox = screen.getByRole('checkbox', { name: /show snow/i })

    fireEvent.click(checkbox)

    await waitFor(() => {
      const map = screen.getByTestId('sfms-map')
      expect(map).toHaveAttribute('data-show-snow', 'false')
    })
  })

  it('should render raster type dropdown next to snow checkbox', async () => {
    renderWithStore(<SFMSInsightsPage />)

    await waitFor(() => {
      const rasterDropdown = screen.getByLabelText(/raster type/i)
      const snowCheckbox = screen.getByRole('checkbox', { name: /show snow/i })

      expect(rasterDropdown).toBeInTheDocument()
      expect(snowCheckbox).toBeInTheDocument()
    })
  })
})
