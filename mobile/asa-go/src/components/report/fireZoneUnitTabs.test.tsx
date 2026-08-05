import { act, fireEvent, render, screen } from '@testing-library/react'
import type { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { FireShape, FireShapeStatusDetail } from '@/api/fbaAPI'
import FireZoneUnitTabs from '@/components/report/FireZoneUnitTabs'
import { useFireCentreDetails } from '@/hooks/useFireCentreDetails'
import { setDateOfInterest } from '@/slices/dateOfInterestSlice'
import { createTestStore } from '@/testUtils'
import type { FireCentre } from '@/types/fireCentre'
import { AdvisoryStatus } from '@/utils/constants'

// Mock calculateStatusColour
vi.mock('@/utils/calculateZoneStatus', () => ({
  calculateStatusColour: () => '#FF0000'
}))

vi.mock('@/hooks/useFireCentreDetails', () => ({
  useFireCentreDetails: vi.fn() as typeof useFireCentreDetails
}))

const mockUseFireCentreDetails = vi.mocked(useFireCentreDetails)
mockUseFireCentreDetails.mockImplementation(
  (fireCentre: FireCentre | undefined, _forDate: DateTime): FireShapeStatusDetail[] => {
    if (!fireCentre) return []
    return [
      {
        fire_shape_id: 1,
        fire_shape_name: 'Zone-1',
        fire_centre_name: fireCentre.name,
        status: AdvisoryStatus.ADVISORY
      },
      {
        fire_shape_id: 2,
        fire_shape_name: 'Zone-2',
        fire_centre_name: fireCentre.name,
        status: AdvisoryStatus.WARNING
      }
    ]
  }
)

describe('FireZoneUnitTabs', () => {
  const mockFireCentre: FireCentre = {
    id: 1,
    name: 'Fire Center 1'
  }

  const mockFireShape: FireShape = {
    fire_shape_id: 1,
    mof_fire_centre_name: 'Fire Center 1',
    mof_fire_zone_name: 'Zone-1'
  }

  const setSelectedFireZoneUnit = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders tabs and children', () => {
    const store = createTestStore()
    render(
      <Provider store={store}>
        <FireZoneUnitTabs
          selectedFireCentre={mockFireCentre}
          selectedFireZoneUnit={mockFireShape}
          setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        >
          <div data-testid="child-content">Child Content</div>
        </FireZoneUnitTabs>
      </Provider>
    )

    expect(screen.getByTestId('zone-1-tab')).toBeInTheDocument()
    expect(screen.getByTestId('zone-2-tab')).toBeInTheDocument()
    expect(screen.getByTestId('child-content')).toBeInTheDocument()
  })

  it('calls setSelectedFireZoneUnit when a tab is clicked', () => {
    const store = createTestStore()
    render(
      <Provider store={store}>
        <FireZoneUnitTabs
          selectedFireCentre={mockFireCentre}
          selectedFireZoneUnit={mockFireShape}
          setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        >
          <div />
        </FireZoneUnitTabs>
      </Provider>
    )

    const tab = screen.getByTestId('zone-2-tab')
    fireEvent.click(tab)

    expect(setSelectedFireZoneUnit).toHaveBeenCalledWith({
      fire_shape_id: 2,
      mof_fire_centre_name: 'Fire Center 1',
      mof_fire_zone_name: 'Zone-2'
    })
  })

  it('passes the date of interest from the store to useFireCentreDetails', () => {
    const store = createTestStore({ dateOfInterest: { dateKey: '2025-08-01' } })
    render(
      <Provider store={store}>
        <FireZoneUnitTabs
          selectedFireCentre={mockFireCentre}
          selectedFireZoneUnit={mockFireShape}
          setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        >
          <div />
        </FireZoneUnitTabs>
      </Provider>
    )

    const [, forDate] = mockUseFireCentreDetails.mock.calls[0]
    expect(forDate?.toISODate()).toBe('2025-08-01')
  })

  it('re-derives the date passed to useFireCentreDetails when the store date changes', () => {
    const store = createTestStore({ dateOfInterest: { dateKey: '2025-08-01' } })
    render(
      <Provider store={store}>
        <FireZoneUnitTabs
          selectedFireCentre={mockFireCentre}
          selectedFireZoneUnit={mockFireShape}
          setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        >
          <div />
        </FireZoneUnitTabs>
      </Provider>
    )

    mockUseFireCentreDetails.mockClear()

    act(() => {
      store.dispatch(setDateOfInterest('2025-08-02'))
    })

    const lastCall = mockUseFireCentreDetails.mock.calls.at(-1)
    expect(lastCall?.[1]?.toISODate()).toBe('2025-08-02')
  })
})
