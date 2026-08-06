import { sendFeedback } from '@sentry/react'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import { HamburgerMenu } from '@/components/HamburgerMenu'
import { type AuthState, initialState as authenticationInitialState } from '@/slices/authenticationSlice'
import { createTestStore } from '@/testUtils'

vi.mock('@sentry/react', () => ({
  sendFeedback: vi.fn()
}))

vi.mock('@sentry/capacitor', () => ({}))

describe('HamburgerMenu', () => {
  const defaultProps = { drawerTop: 60, drawerHeight: 740 }
  const authenticatedState: AuthState = {
    ...authenticationInitialState,
    email: 'user@example.com',
    sessionMode: 'authenticated'
  }

  const renderMenu = (connected = true, authentication = authenticatedState) =>
    render(
      <Provider
        store={createTestStore({
          authentication,
          networkStatus: {
            networkStatus: {
              connected,
              connectionType: connected ? 'wifi' : 'none'
            }
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

  it('allows a public user to send feedback without a prefilled email', async () => {
    const mockSendFeedback = vi.mocked(sendFeedback).mockResolvedValue('event-id')
    const user = userEvent.setup()
    renderMenu(true, {
      ...authenticationInitialState,
      sessionMode: 'guest'
    })

    await user.click(screen.getByRole('button', { name: /open menu/i }))
    await user.click(await screen.findByText('Submit Feedback'))

    expect(await screen.findByRole('dialog', { name: 'Submit Feedback' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Email' })).toHaveValue('')

    await user.type(screen.getByRole('textbox', { name: 'Description' }), 'Public user feedback.')
    await user.click(screen.getByRole('button', { name: 'Send Feedback' }))

    await vi.waitFor(() => {
      expect(mockSendFeedback).toHaveBeenCalledWith(
        {
          email: undefined,
          message: 'Public user feedback.',
          name: undefined
        },
        { includeReplay: true }
      )
    })
    expect(await screen.findByText('Thank you for your feedback.')).toBeInTheDocument()
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

  it('disables feedback while offline', async () => {
    renderMenu(false)
    fireEvent.click(screen.getByRole('button', { name: /open menu/i }))

    const submitFeedback = await screen.findByRole('button', { name: 'Submit Feedback' })
    expect(submitFeedback).toHaveAttribute('aria-disabled', 'true')
    fireEvent.click(submitFeedback)

    expect(screen.queryByRole('dialog', { name: 'Submit Feedback' })).not.toBeInTheDocument()
  })
})
