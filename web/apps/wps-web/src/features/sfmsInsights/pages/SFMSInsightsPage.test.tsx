import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { SFMSInsightsPage } from './SFMSInsightsPage'
import { Provider } from 'react-redux'
import { createTestStore } from '@/test/testUtils'
import { getMostRecentProcessedSnowByDate } from '@/api/snow'
import { getSFMSBounds } from '@/api/fbaAPI'
import { getDateTimeNowPST } from '@/utils/date'
import { DateTime } from 'luxon'
import { Mock } from 'vitest'

vi.mock('@/api/snow', () => ({
  getMostRecentProcessedSnowByDate: vi.fn()
}))

vi.mock('@/utils/date', () => ({
  getDateTimeNowPST: vi.fn()
}))

vi.mock('@/api/fbaAPI', () => ({
  getSFMSBounds: vi.fn()
}))

vi.mock('@/features/sfmsInsights/components/map/SFMSMap', () => {
  return {
    default: ({
      showSnow,
      snowDate,
      rasterDate
    }: {
      showSnow: boolean
      snowDate: DateTime | null
      rasterDate: DateTime | null
    }) => (
      <div
        data-testid="sfms-map"
        data-show-snow={showSnow}
        data-snow-date={snowDate?.toISO() ?? 'null'}
        data-raster-date={rasterDate?.toISO() ?? 'null'}
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
  default: ({
    date,
    updateDate,
    historicalMinDate,
    historicalMaxDate,
    currentYearMinDate,
    currentYearMaxDate,
    disabled
  }: {
    date: DateTime | null
    updateDate: (date: DateTime) => void
    historicalMinDate?: DateTime
    historicalMaxDate?: DateTime
    currentYearMinDate?: DateTime
    currentYearMaxDate?: DateTime
    disabled?: boolean
  }) => (
    <div data-testid="date-picker" data-disabled={disabled}>
      <button data-testid="change-date-button" onClick={() => updateDate(DateTime.fromISO('2025-12-15'))}>
        Change Date
      </button>
      <span data-testid="current-date">{date?.toISODate() ?? 'null'}</span>
      <span data-testid="historical-min-date">{historicalMinDate?.toISODate() ?? 'null'}</span>
      <span data-testid="historical-max-date">{historicalMaxDate?.toISODate() ?? 'null'}</span>
      <span data-testid="current-year-min-date">{currentYearMinDate?.toISODate() ?? 'null'}</span>
      <span data-testid="current-year-max-date">{currentYearMaxDate?.toISODate() ?? 'null'}</span>
    </div>
  )
}))

vi.mock('@/features/sfmsInsights/components/RasterTypeDropdown', () => ({
  default: ({ rasterDataAvailable }: { rasterDataAvailable?: boolean }) => (
    <div data-testid="raster-type-dropdown" data-raster-data-available={rasterDataAvailable}>
      Mock Raster Dropdown
    </div>
  )
}))

describe('SFMSInsightsPage', () => {
  const dateTimeNow = DateTime.fromISO('2025-11-02')
  const dateTimeNowPlusTen = dateTimeNow.plus({ days: 10 })
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

  const defaultAuthentication = {
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

  const defaultRunDates = {
    loading: false,
    error: null,
    runDates: [],
    mostRecentRunDate: null,
    sfmsBoundsError: null,
    sfmsBoundsLoading: false,
    sfmsBounds: {
      '2024': {
        forecast: {
          minimum: '2024-01-01',
          maximum: '2024-12-31'
        }
      },
      '2025': {
        forecast: {
          minimum: '2025-01-01',
          maximum: '2025-11-02'
        }
      }
    }
  }

  const renderWithStore = (sfmsBounds?: any) => {
    const store = createTestStore({
      authentication: defaultAuthentication,
      runDates: {
        ...defaultRunDates,
        ...(sfmsBounds !== undefined && { sfmsBounds, sfmsBoundsLoading: false })
      }
    })
    return render(<Provider store={store}>{<SFMSInsightsPage />}</Provider>)
  }

  const waitForPageLoad = async () => {
    // Wait for SFMS bounds loading to complete
    // Either the loading spinner disappears, or the date picker appears
    await waitFor(
      () => {
        const hasDatePicker = screen.queryByTestId('date-picker') !== null
        const hasNoSpinner = screen.queryByRole('progressbar') === null
        expect(hasDatePicker || hasNoSpinner).toBe(true)
      },
      { timeout: 3000 }
    )
  }

  beforeEach(() => {
    vi.clearAllMocks()
    ;(getMostRecentProcessedSnowByDate as Mock).mockResolvedValue({
      forDate: DateTime.fromISO('2025-11-02'),
      processedDate: DateTime.fromISO('2025-11-02'),
      snowSource: 'viirs'
    })
    // Mock getDateTimeNowPST to return a date in 2025
    ;(getDateTimeNowPST as Mock).mockReturnValue(dateTimeNow)
    // Mock getSFMSBounds API call
    ;(getSFMSBounds as Mock).mockResolvedValue({
      sfms_bounds: {
        '2024': {
          forecast: {
            minimum: '2024-01-01',
            maximum: '2024-12-31'
          }
        },
        '2025': {
          forecast: {
            minimum: '2025-01-01',
            maximum: '2025-11-02'
          }
        }
      }
    })
  })

  it('should load rasterDate from SFMS bounds in store', async () => {
    renderWithStore()
    await waitForPageLoad()

    // Verify that the rasterDate was set from the sfmsBounds in the store
    const map = screen.getByTestId('sfms-map')
    const rasterDate = map.dataset.rasterDate
    expect(rasterDate).toContain('2025-11-02')
  })

  it('should set date picker max date based on SFMS bounds', async () => {
    renderWithStore()
    await waitForPageLoad()

    // The date picker should be rendered with max date from SFMS bounds (2025-11-02)
    const datePicker = screen.getByTestId('date-picker')
    expect(datePicker).toBeInTheDocument()
  })

  it('should render the snow checkbox', async () => {
    renderWithStore()
    await waitForPageLoad()
    const checkbox = screen.getByRole('checkbox', { name: /show latest snow/i })
    expect(checkbox).toBeInTheDocument()
  })

  it('should have the snow checkbox checked by default', async () => {
    renderWithStore()
    await waitForPageLoad()
    const checkbox = screen.getByRole('checkbox', { name: /show latest snow/i }) as HTMLInputElement
    expect(checkbox.checked).toBe(true)
  })

  it('should toggle snow checkbox when clicked', async () => {
    renderWithStore()
    await waitForPageLoad()

    const checkbox = screen.getByRole('checkbox', { name: /show latest snow/i }) as HTMLInputElement
    expect(checkbox.checked).toBe(true)

    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(false)

    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(true)
  })

  it('should pass showSnow prop to SFMSMap when checkbox is checked', async () => {
    renderWithStore()
    await waitForPageLoad()

    const map = screen.getByTestId('sfms-map')
    expect(map).toHaveAttribute('data-show-snow', 'true')
  })

  it('should pass showSnow=false to SFMSMap when checkbox is unchecked', async () => {
    renderWithStore()
    await waitForPageLoad()

    const checkbox = screen.getByRole('checkbox', { name: /show latest snow/i })
    fireEvent.click(checkbox)

    await waitFor(() => {
      const map = screen.getByTestId('sfms-map')
      expect(map).toHaveAttribute('data-show-snow', 'false')
    })
  })

  it('should render raster type dropdown next to snow checkbox', async () => {
    renderWithStore()
    await waitForPageLoad()

    const rasterDropdown = screen.getByTestId('raster-type-dropdown')
    const snowCheckbox = screen.getByRole('checkbox', { name: /show latest snow/i })

    expect(rasterDropdown).toBeInTheDocument()
    expect(snowCheckbox).toBeInTheDocument()
  })

  it('should fetch snow data on mount with initial rasterDate', async () => {
    renderWithStore()
    await waitForPageLoad()

    expect(getMostRecentProcessedSnowByDate).toHaveBeenCalledWith(DateTime.fromISO('2025-11-02'))
  })

  it('should pass fetched snow date to SFMSMap', async () => {
    renderWithStore()
    await waitForPageLoad()

    const map = screen.getByTestId('sfms-map')
    const snowDate = map.dataset.snowDate
    expect(snowDate).toContain('2025-11-02T00:00:00')
  })

  it('should display snow date in checkbox label when available', async () => {
    renderWithStore()
    await waitForPageLoad()

    const checkbox = screen.getByRole('checkbox', { name: /show latest snow: nov 2, 2025/i })
    expect(checkbox).toBeInTheDocument()
  })

  it('should display "Show Latest Snow" without date when no snow data available', async () => {
    ;(getMostRecentProcessedSnowByDate as Mock).mockResolvedValue(null)

    renderWithStore()
    await waitForPageLoad()

    const checkbox = screen.getByRole('checkbox', { name: 'Show Latest Snow' })
    expect(checkbox).toBeInTheDocument()
  })

  it('should refetch snow data when rasterDate changes', async () => {
    ;(getMostRecentProcessedSnowByDate as Mock)
      .mockResolvedValueOnce({
        forDate: DateTime.fromISO('2025-11-02'),
        processedDate: DateTime.fromISO('2025-11-02'),
        snowSource: 'viirs'
      })
      .mockResolvedValueOnce({
        forDate: DateTime.fromISO('2025-12-15'),
        processedDate: DateTime.fromISO('2025-12-15'),
        snowSource: 'viirs'
      })

    renderWithStore()
    await waitForPageLoad()

    // Wait for initial fetch
    expect(getMostRecentProcessedSnowByDate).toHaveBeenCalledWith(DateTime.fromISO('2025-11-02'))

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

  it('should set maxDate from latestSFMSBounds.maximum', async () => {
    renderWithStore()
    await waitForPageLoad()

    const maxDate = screen.getByTestId('historical-max-date')
    expect(maxDate.textContent).toBe(dateTimeNowPlusTen.toISODate())
  })

  it('should set minDate from earliestSFMSBounds.minimum', async () => {
    renderWithStore()
    await waitForPageLoad()

    const minDate = screen.getByTestId('historical-min-date')
    expect(minDate.textContent).toBe('2024-01-01')
  })

  it('should pass both min and max dates to ASADatePicker', async () => {
    renderWithStore()
    await waitForPageLoad()

    const minDate = screen.getByTestId('current-year-min-date')
    const maxDate = screen.getByTestId('current-year-max-date')

    expect(minDate.textContent).toBe('2024-01-01')
    expect(maxDate.textContent).toBe(dateTimeNowPlusTen.toISODate())
  })

  it('should update min bounds when latestBounds changes', async () => {
    renderWithStore({
      '2025': {
        forecast: {
          minimum: '2025-05-01',
          maximum: '2025-10-15'
        }
      }
    })
    await waitForPageLoad()

    const minDate = screen.getByTestId('historical-min-date')
    expect(minDate.textContent).toBe('2025-05-01')
  })

  it('should set rasterDate to today when latestBounds is null', async () => {
    // Mock getSFMSBounds to return null
    ;(getSFMSBounds as Mock).mockResolvedValueOnce({ sfms_bounds: null })

    renderWithStore(null)

    // Wait for fetch to complete
    await waitFor(() => {
      expect(screen.getByTestId('date-picker')).toBeInTheDocument()
    })

    const currentDate = screen.getByTestId('current-date')
    // Should default to today's date (mocked as 2025-11-02)
    expect(currentDate.textContent).toBe('2025-11-02')

    // Min/max dates should use default values
    const minDate = screen.getByTestId('historical-min-date')
    const maxDate = screen.getByTestId('historical-max-date')
    expect(minDate.textContent).toBe('2025-01-01')
    expect(maxDate.textContent).toBe('2025-11-12')
  })

  it('should set rasterDate to today when latestBounds.maximum is empty', async () => {
    renderWithStore({
      '2025': {
        forecast: {
          minimum: '2025-05-01',
          maximum: ''
        }
      }
    })

    const datePicker = screen.getByTestId('date-picker')
    expect(datePicker).toBeInTheDocument()

    const currentDate = screen.getByTestId('current-date')
    // Should default to today's date (mocked as 2025-11-02)
    expect(currentDate.textContent).toBe('2025-11-02')

    // minDate should be set from bounds
    const minDate = screen.getByTestId('historical-min-date')
    expect(minDate.textContent).toBe('2025-05-01')
  })

  it('should not set minDate when earliestBounds.minimum is empty', async () => {
    renderWithStore({
      '2025': {
        forecast: {
          minimum: '',
          maximum: '2025-10-15'
        }
      }
    })
    await waitForPageLoad()

    const minDate = screen.getByTestId('historical-min-date')

    // minDate should use default value since earliestBounds.minimum is empty
    expect(minDate.textContent).toBe('2025-01-01')
  })

  it('should set rasterDate to today when all years have empty maximum', async () => {
    renderWithStore({
      '2024': {
        forecast: {
          minimum: '2024-01-01',
          maximum: ''
        }
      },
      '2025': {
        forecast: {
          minimum: '',
          maximum: ''
        }
      }
    })

    const datePicker = screen.getByTestId('date-picker')
    expect(datePicker).toBeInTheDocument()

    const currentDate = screen.getByTestId('current-date')
    // Should default to today's date (mocked as 2025-11-02)
    expect(currentDate.textContent).toBe('2025-11-02')

    // minDate should be set from 2024 bounds
    const minDate = screen.getByTestId('historical-min-date')
    expect(minDate.textContent).toBe('2024-01-01')
  })

  it('should disable raster dropdown options when no SFMS bounds data available', async () => {
    renderWithStore(null)

    const dropdown = screen.getByTestId('raster-type-dropdown')
    expect(dropdown).toHaveAttribute('data-raster-data-available', 'false')
  })

  it('should enable raster dropdown options when SFMS bounds data available', async () => {
    renderWithStore()
    await waitForPageLoad()

    const dropdown = screen.getByTestId('raster-type-dropdown')
    expect(dropdown).toHaveAttribute('data-raster-data-available', 'true')
  })
})
