import { render, screen } from '@testing-library/react'
import { useSelector } from 'react-redux'
import { vi } from 'vitest'
import type { FireCenterDropdownProps } from '@/components/FireCenterDropdown'
import Advisory from '@/components/report/Advisory'
import type { AdvisoryTextProps } from '@/components/report/AdvisoryText'
import type { FireZoneUnitTabsProps } from '@/components/report/FireZoneUnitTabs'
import type { FireCentre } from '@/types/fireCentre'

// Mock child components with proper props
vi.mock('@/components/TodayTomorrowSwitch', () => ({
  default: () => <div data-testid="today-tomorrow-switch">Today/Tomorrow</div>
}))

vi.mock('@/components/FireCenterDropdown', () => ({
  default: ({ fireCentreOptions }: FireCenterDropdownProps) => (
    <div data-testid="fire-center-dropdown">Options: {fireCentreOptions.length}</div>
  )
}))

vi.mock('@/components/report/FireZoneUnitTabs', () => ({
  default: ({ children }: FireZoneUnitTabsProps) => <div data-testid="fire-zone-tabs">{children}</div>
}))

vi.mock('@/components/report/AdvisoryText', () => ({
  default: (_: AdvisoryTextProps) => <div data-testid="advisory-text">Advisory Text Content</div>
}))

// Mock Redux selector
vi.mock('react-redux', async importOriginal => {
  const actual = await importOriginal<typeof import('react-redux')>()
  return {
    ...actual,
    useSelector: vi.fn()
  }
})

describe('Advisory Component', () => {
  const mockFireCentres: FireCentre[] = [
    { name: 'Center 1', id: 1 },
    { name: 'Center 2', id: 2 }
  ]

  const setSelectedFireCentre = vi.fn()
  const setSelectedFireZoneUnit = vi.fn()

  beforeEach(() => {
    vi.mocked(useSelector).mockReturnValue({ fireCentres: mockFireCentres })
  })

  it('renders all key sections and child components', () => {
    render(
      <Advisory
        selectedFireCentre={mockFireCentres[0]}
        setSelectedFireCentre={setSelectedFireCentre}
        selectedFireZoneUnit={undefined}
        setSelectedFireZoneUnit={setSelectedFireZoneUnit}
      />
    )

    expect(screen.getByTestId('asa-go-advisory')).toBeInTheDocument()
    expect(screen.getByTestId('advisory-control-container')).toBeInTheDocument()
    expect(screen.getByTestId('today-tomorrow-switch')).toBeInTheDocument()
    expect(screen.getByTestId('fire-center-dropdown')).toHaveTextContent('Options: 2')
    expect(screen.getByTestId('fire-zone-tabs')).toBeInTheDocument()
    expect(screen.getByTestId('advisory-text')).toHaveTextContent('Advisory Text Content')
  })
})
