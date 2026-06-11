import { fireEvent, render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { HamburgerMenu } from '@/components/HamburgerMenu'

vi.mock('@sentry/react', () => ({
  getFeedback: vi.fn()
}))

vi.mock('@sentry/capacitor', () => ({}))

import { getFeedback } from '@sentry/react'

const mockGetFeedback = getFeedback as ReturnType<typeof vi.fn>

describe('HamburgerMenu', () => {
  const defaultProps = { drawerTop: 60, drawerHeight: 740 }

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders the menu button', () => {
    mockGetFeedback.mockReturnValue(undefined)
    render(<HamburgerMenu {...defaultProps} />)
    expect(screen.getByRole('button', { name: /open menu/i })).toBeInTheDocument()
  })

  it('opens the Sentry feedback dialog when Submit Feedback is clicked', async () => {
    const mockForm = { appendToDom: vi.fn(), open: vi.fn() }
    const mockCreateForm = vi.fn().mockResolvedValue(mockForm)
    mockGetFeedback.mockReturnValue({ createForm: mockCreateForm })

    render(<HamburgerMenu {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /open menu/i }))

    const submitFeedback = await screen.findByText('Submit Feedback')
    fireEvent.click(submitFeedback)

    await vi.waitFor(
      () => {
        expect(mockCreateForm).toHaveBeenCalled()
        expect(mockForm.appendToDom).toHaveBeenCalled()
        expect(mockForm.open).toHaveBeenCalled()
      },
      { timeout: 1000 }
    )
  })

  it('opens external links in a new tab', async () => {
    const mockOpen = vi.spyOn(window, 'open').mockImplementation(() => null)
    mockGetFeedback.mockReturnValue(undefined)

    render(<HamburgerMenu {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /open menu/i }))

    const homeLink = await screen.findByText('Home')
    fireEvent.click(homeLink)

    expect(mockOpen).toHaveBeenCalledWith('https://psu.nrs.gov.bc.ca/', '_blank', 'noopener,noreferrer')
    mockOpen.mockRestore()
  })

  it('does not open the feedback form when the drawer closes without Submit Feedback being clicked', async () => {
    const mockForm = { appendToDom: vi.fn(), open: vi.fn() }
    const mockCreateForm = vi.fn().mockResolvedValue(mockForm)
    mockGetFeedback.mockReturnValue({ createForm: mockCreateForm })

    render(<HamburgerMenu {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /open menu/i }))

    const closeButton = await screen.findByRole('button', { name: /close settings/i })
    fireEvent.click(closeButton)

    await vi.waitFor(
      () => {
        expect(mockCreateForm).not.toHaveBeenCalled()
        expect(mockForm.appendToDom).not.toHaveBeenCalled()
        expect(mockForm.open).not.toHaveBeenCalled()
      },
      { timeout: 1000 }
    )
  })

  it('does not throw when getFeedback returns undefined and Submit Feedback is clicked', async () => {
    mockGetFeedback.mockReturnValue(undefined)

    render(<HamburgerMenu {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /open menu/i }))

    const submitFeedback = await screen.findByText('Submit Feedback')
    expect(() => fireEvent.click(submitFeedback)).not.toThrow()
  })
})
