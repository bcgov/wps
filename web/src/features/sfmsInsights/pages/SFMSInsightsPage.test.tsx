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
    default: ({ showSnow, snowDate, rasterDate }: { showSnow: boolean; snowDate: DateTime | null; rasterDate: DateTime }) => (
      <div
        data-testid="sfms-map"
        data-show-snow={showSnow}
        data-snow-date={snowDate?.toISO() ?? 'null'}
        data-raster-date={rasterDate.toISO()}
      >
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

vi.mock('@/features/fba/components/ASADatePicker', () => ({
  default: ({ date, updateDate }: { date: DateTime; updateDate: (date: DateTime) => void }) => (
    <div data-testid="date-picker">
      <button data-testid="change-date-button" onClick={() => updateDate(DateTime.fromISO('2025-12-15'))}>
        Change Date
      </button>
      <span data-testid="current-date">{date.toISODate()}</span>
    </div>
  )
}))

vi.mock('@/features/sfmsInsights/components/RasterTypeDropdown', () => ({
  default: () => <div data-testid="raster-type-dropdown">Mock Raster Dropdown</div>
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
  globalThis.ResizeObserver = ResizeObserver

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
      const rasterDropdown = screen.getByTestId('raster-type-dropdown')
      const snowCheckbox = screen.getByRole('checkbox', { name: /show snow/i })

      expect(rasterDropdown).toBeInTheDocument()
      expect(snowCheckbox).toBeInTheDocument()
    })
  })

  it('should fetch snow data on mount with initial rasterDate', async () => {
    renderWithStore(<SFMSInsightsPage />)

    await waitFor(() => {
      expect(getMostRecentProcessedSnowByDate).toHaveBeenCalledWith(DateTime.fromISO('2025-11-02'))
    })
  })

  it('should pass fetched snow date to SFMSMap', async () => {
    renderWithStore(<SFMSInsightsPage />)

    await waitFor(() => {
      const map = screen.getByTestId('sfms-map')
      const snowDate = map.dataset.snowDate
      expect(snowDate).toContain('2025-11-02T00:00:00')
    })
  })

  it('should display snow date in checkbox label when available', async () => {
    renderWithStore(<SFMSInsightsPage />)

    await waitFor(() => {
      const checkbox = screen.getByRole('checkbox', { name: /show snow \(nov 2, 2025\)/i })
      expect(checkbox).toBeInTheDocument()
    })
  })

  it('should display "Show Snow" without date when no snow data available', async () => {
    ;(getMostRecentProcessedSnowByDate as Mock).mockResolvedValue(null)

    renderWithStore(<SFMSInsightsPage />)

    await waitFor(() => {
      const checkbox = screen.getByRole('checkbox', { name: 'Show Snow' })
      expect(checkbox).toBeInTheDocument()
    })
  })

  it('should refetch snow data when rasterDate changes', async () => {
    ;(getMostRecentProcessedSnowByDate as Mock).mockResolvedValueOnce({
      forDate: DateTime.fromISO('2025-11-02'),
      processedDate: DateTime.fromISO('2025-11-02'),
      snowSource: 'viirs'
    }).mockResolvedValueOnce({
      forDate: DateTime.fromISO('2025-12-15'),
      processedDate: DateTime.fromISO('2025-12-15'),
      snowSource: 'viirs'
    })

    renderWithStore(<SFMSInsightsPage />)

    // Wait for initial fetch
    await waitFor(() => {
      expect(getMostRecentProcessedSnowByDate).toHaveBeenCalledWith(DateTime.fromISO('2025-11-02'))
    })

    // Change the date
    const changeDateButton = screen.getByTestId('change-date-button')
    fireEvent.click(changeDateButton)

    // Verify snow data is refetched with the new date
    await waitFor(() => {
      expect(getMostRecentProcessedSnowByDate).toHaveBeenCalledWith(DateTime.fromISO('2025-12-15'))
      expect(getMostRecentProcessedSnowByDate).toHaveBeenCalledTimes(2)
    })

    // Verify the new snow date is passed to the map
    await waitFor(() => {
      const map = screen.getByTestId('sfms-map')
      const snowDate = map.dataset.snowDate
      expect(snowDate).toContain('2025-12-15T00:00:00')
    })
  })
})
