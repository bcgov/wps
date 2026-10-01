import { fireEvent, render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { AboutDataPanel } from '@/components/AboutDataPanel'
import { useIsTablet } from '@/hooks/useIsTablet'

vi.mock('@/hooks/useIsTablet', () => ({ useIsTablet: vi.fn() }))

describe('AboutDataPanel', () => {
  beforeEach(() => {
    vi.mocked(useIsTablet).mockReturnValue(false)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the information sections', () => {
    render(<AboutDataPanel onBack={vi.fn()} onClose={vi.fn()} />)

    expect(screen.getByRole('heading', { name: 'About This Data', level: 2 })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Fire Behaviour Advisory', level: 3 })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Fire Behaviour Warning', level: 3 })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Fuel types in the text bulletin', level: 3 })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Fuel types in the Profile tab', level: 3 })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Portion under advisory', level: 3 })).toBeInTheDocument()
  })

  it('opens the fuel types link in a new tab', () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)
    render(<AboutDataPanel onBack={vi.fn()} onClose={vi.fn()} />)

    fireEvent.click(screen.getByRole('link', { name: 'fuel types' }))

    expect(open).toHaveBeenCalledWith(
      'https://cwfis.cfs.nrcan.gc.ca/en/background/fuel-types?fuel=c1',
      '_blank',
      'noopener,noreferrer'
    )
  })

  it.each([{ isTablet: false }, { isTablet: true }])(
    'uses the expected panel width for tablet=$isTablet',
    ({ isTablet }) => {
      vi.mocked(useIsTablet).mockReturnValue(isTablet)
      render(<AboutDataPanel onBack={vi.fn()} onClose={vi.fn()} />)

      const panel = screen.getByRole('heading', { name: 'About This Data' }).parentElement?.parentElement
      expect(panel).toHaveStyle({ width: isTablet ? '460px' : `${window.innerWidth}px` })
    }
  )
})
