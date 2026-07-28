import { ThemeProvider } from '@mui/material/styles'
import { act, render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { describe, expect, it, vi } from 'vitest'
import type { FireShape, FireZoneTPIStats } from '@/api/fbaAPI'
import FireZoneUnitSummary from '@/components/profile/FireZoneUnitSummary'
import { useFilteredHFIStatsForDate, useTPIStatsForDate } from '@/hooks/dataHooks'
import { setDateOfInterest } from '@/slices/dateOfInterestSlice'
import { createTestStore } from '@/testUtils'
import { theme } from '@/theme'
import type { FireCentre } from '@/types/fireCentre'

// Mock child components
vi.mock('@/components/profile/FuelSummary', () => ({
  default: ({ selectedFireZoneUnit }: { selectedFireZoneUnit: FireShape | undefined }) => (
    <div data-testid="fuel-summary">
      {selectedFireZoneUnit ? `Fuel Summary for ${selectedFireZoneUnit.mof_fire_zone_name}` : 'No fuel summary'}
    </div>
  )
}))

vi.mock('@/components/profile/ElevationStatus', () => ({
  default: ({ tpiStats }: { tpiStats: Required<FireZoneTPIStats> }) => (
    <div data-testid="elevation-status">{`Elevation Status for zone ${tpiStats.fire_zone_id}`}</div>
  )
}))

// Mock hooks
vi.mock('@/hooks/dataHooks', () => ({
  useFilteredHFIStatsForDate: vi.fn(),
  useTPIStatsForDate: vi.fn()
}))

describe('FireZoneUnitSummary', () => {
  const mockFireCentre: FireCentre = {
    id: 1,
    name: 'Test Fire Centre'
  }

  const mockFireZoneUnit: FireShape = {
    fire_shape_id: 1,
    mof_fire_zone_name: 'Test Zone',
    mof_fire_centre_name: 'Test Centre',
    area_sqm: 1000
  }

  const renderWithProvider = (component: React.ReactElement<any>, store = createTestStore()) => {
    return render(
      <Provider store={store}>
        <ThemeProvider theme={theme}>{component}</ThemeProvider>
      </Provider>
    )
  }

  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks()
  })

  it('should render empty div when selectedFireZoneUnit is undefined', () => {
    renderWithProvider(<FireZoneUnitSummary selectedFireCentre={mockFireCentre} selectedFireZoneUnit={undefined} />)

    const emptyDiv = screen.getByTestId('fire-zone-unit-summary-empty')
    expect(emptyDiv).toBeInTheDocument()
  })

  it('should render fire zone unit summary when selectedFireZoneUnit is provided', () => {
    renderWithProvider(
      <FireZoneUnitSummary selectedFireCentre={mockFireCentre} selectedFireZoneUnit={mockFireZoneUnit} />
    )

    const summary = screen.getByTestId('fire-zone-unit-summary')
    expect(summary).toBeInTheDocument()
  })

  it('should display the fire zone name as title', () => {
    renderWithProvider(
      <FireZoneUnitSummary selectedFireCentre={mockFireCentre} selectedFireZoneUnit={mockFireZoneUnit} />
    )

    const title = screen.getByTestId('fire-zone-title-tabs')
    expect(title).toBeInTheDocument()
    expect(title).toHaveTextContent('Test Zone')
  })

  it('should render FuelSummary component', () => {
    renderWithProvider(
      <FireZoneUnitSummary selectedFireCentre={mockFireCentre} selectedFireZoneUnit={mockFireZoneUnit} />
    )

    const fuelSummary = screen.getByTestId('fuel-summary')
    expect(fuelSummary).toBeInTheDocument()
    expect(fuelSummary).toHaveTextContent('Fuel Summary for Test Zone')
  })

  it('should show no elevation information message when TPI stats are incomplete', () => {
    renderWithProvider(
      <FireZoneUnitSummary selectedFireCentre={mockFireCentre} selectedFireZoneUnit={mockFireZoneUnit} />
    )

    expect(screen.getByText('No elevation information available.')).toBeInTheDocument()
  })

  it('should have correct styling', () => {
    renderWithProvider(
      <FireZoneUnitSummary selectedFireCentre={mockFireCentre} selectedFireZoneUnit={mockFireZoneUnit} />
    )

    const summary = screen.getByTestId('fire-zone-unit-summary')
    expect(summary).toHaveStyle({
      width: '100%'
    })
    // The backgroundColor and overflowY are applied via MUI's sx prop
    // so we just verify the component renders with the correct structure
    expect(summary).toBeInTheDocument()
  })

  it('should render Stack container with correct props', () => {
    const { container } = renderWithProvider(
      <FireZoneUnitSummary selectedFireCentre={mockFireCentre} selectedFireZoneUnit={mockFireZoneUnit} />
    )

    const stackContainer = container.querySelector('.MuiStack-root')
    expect(stackContainer).toBeInTheDocument()
  })

  it('should handle missing fire center', () => {
    renderWithProvider(<FireZoneUnitSummary selectedFireCentre={undefined} selectedFireZoneUnit={undefined} />)

    const defaultMessage = screen.getByTestId('default-message')
    expect(defaultMessage).toBeInTheDocument()
    expect(defaultMessage).toHaveTextContent('Please select a fire centre.')
  })

  it('passes the date of interest from the store to the data hooks', () => {
    const store = createTestStore({ dateOfInterest: { dateKey: '2025-08-01' } })
    renderWithProvider(
      <FireZoneUnitSummary selectedFireCentre={mockFireCentre} selectedFireZoneUnit={mockFireZoneUnit} />,
      store
    )

    const hfiDate = vi.mocked(useFilteredHFIStatsForDate).mock.calls.at(-1)?.[0]
    const tpiDate = vi.mocked(useTPIStatsForDate).mock.calls.at(-1)?.[0]
    expect(hfiDate?.toISODate()).toBe('2025-08-01')
    expect(tpiDate?.toISODate()).toBe('2025-08-01')
  })

  it('re-derives the date passed to the data hooks when the store date changes', () => {
    const store = createTestStore({ dateOfInterest: { dateKey: '2025-08-01' } })
    renderWithProvider(
      <FireZoneUnitSummary selectedFireCentre={mockFireCentre} selectedFireZoneUnit={mockFireZoneUnit} />,
      store
    )

    vi.mocked(useFilteredHFIStatsForDate).mockClear()
    vi.mocked(useTPIStatsForDate).mockClear()

    act(() => {
      store.dispatch(setDateOfInterest('2025-08-02'))
    })

    const hfiDate = vi.mocked(useFilteredHFIStatsForDate).mock.calls.at(-1)?.[0]
    const tpiDate = vi.mocked(useTPIStatsForDate).mock.calls.at(-1)?.[0]
    expect(hfiDate?.toISODate()).toBe('2025-08-02')
    expect(tpiDate?.toISODate()).toBe('2025-08-02')
  })
})
