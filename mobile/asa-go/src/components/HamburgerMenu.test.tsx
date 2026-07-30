import { fireEvent, render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import { HamburgerMenu } from '@/components/HamburgerMenu'
import { initialState as authenticationInitialState } from '@/slices/authenticationSlice'
import { createTestStore } from '@/testUtils'

vi.mock('@sentry/react', () => ({
  sendFeedback: vi.fn()
}))

vi.mock('@sentry/capacitor', () => ({}))

describe('HamburgerMenu', () => {
  const defaultProps = { drawerTop: 60, drawerHeight: 740 }

  const renderMenu = () =>
    render(
      <Provider
        store={createTestStore({
          authentication: {
            ...authenticationInitialState,
            email: 'user@example.com'
          }
        })}
      >
        <HamburgerMenu {...defaultProps} />
      </Provider>
    )

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders the menu button', () => {
    renderMenu()
    expect(screen.getByRole('button', { name: /open menu/i })).toBeInTheDocument()
  })

  it('opens the feedback dialog when Submit Feedback is clicked', async () => {
    renderMenu()
    fireEvent.click(screen.getByRole('button', { name: /open menu/i }))

    fireEvent.click(await screen.findByText('Submit Feedback'))

    expect(await screen.findByRole('dialog', { name: 'Submit Feedback' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Email' })).toHaveValue('user@example.com')
  })

  it('opens external links in a new tab', async () => {
    const mockOpen = vi.spyOn(globalThis, 'open').mockImplementation(() => null)

    renderMenu()
    fireEvent.click(screen.getByRole('button', { name: /open menu/i }))

    const homeLink = await screen.findByText('Home')
    fireEvent.click(homeLink)

    expect(mockOpen).toHaveBeenCalledWith('https://psu.nrs.gov.bc.ca/', '_blank', 'noopener,noreferrer')
    mockOpen.mockRestore()
  })

  it('does not open the feedback dialog when the drawer closes without Submit Feedback being clicked', async () => {
    renderMenu()
    fireEvent.click(screen.getByRole('button', { name: /open menu/i }))

    fireEvent.click(await screen.findByRole('button', { name: /close settings/i }))

    await vi.waitFor(() => {
      expect(screen.queryByRole('dialog', { name: 'Submit Feedback' })).not.toBeInTheDocument()
    })
  })
})
