import { sendFeedback } from '@sentry/react'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ComponentProps } from 'react'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import { FeedbackDialog } from '@/components/FeedbackDialog'
import { createTestStore } from '@/testUtils'

vi.mock('@sentry/react', () => ({
  sendFeedback: vi.fn()
}))

const mockSendFeedback = vi.mocked(sendFeedback)

const renderFeedbackDialog = (props: Partial<ComponentProps<typeof FeedbackDialog>> = {}) =>
  render(
    <Provider store={createTestStore()}>
      <FeedbackDialog isOnline onClose={vi.fn()} open {...props} />
    </Provider>
  )

describe('FeedbackDialog', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('prefills the authenticated email and keeps close controls available', () => {
    renderFeedbackDialog({ defaultEmail: 'user@example.com' })

    expect(screen.getByRole('textbox', { name: 'Email' })).toHaveValue('user@example.com')
    expect(screen.getByRole('button', { name: 'close feedback' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })

  it.each(['Name', 'Description'])('keeps the %s label above the outline when focus changes', fieldName => {
    renderFeedbackDialog()
    const field = screen.getByRole('textbox', { name: fieldName })
    const label = document.querySelector(`label[for="${field.id}"]`)

    expect(label).toHaveAttribute('data-shrink', 'true')
    fireEvent.focus(field)
    expect(label).toHaveAttribute('data-shrink', 'true')
    fireEvent.blur(field)
    expect(label).toHaveAttribute('data-shrink', 'true')
    fireEvent.focus(field)
    expect(label).toHaveAttribute('data-shrink', 'true')
  })

  it('sends feedback through Sentry and closes the form', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    mockSendFeedback.mockResolvedValue('event-id')
    renderFeedbackDialog({ defaultEmail: 'user@example.com', onClose })

    fireEvent.change(screen.getByRole('textbox', { name: 'Name' }), { target: { value: 'A User' } })
    fireEvent.change(screen.getByRole('textbox', { name: 'Description' }), {
      target: { value: 'The map did not load.' }
    })
    await user.click(screen.getByRole('button', { name: 'Send Feedback' }))

    await vi.waitFor(() => {
      expect(mockSendFeedback).toHaveBeenCalledWith(
        {
          email: 'user@example.com',
          message: 'The map did not load.',
          name: 'A User'
        },
        { includeReplay: true }
      )
      expect(onClose).toHaveBeenCalled()
    })
    expect(await screen.findByText('Thank you for your feedback.')).toBeInTheDocument()
  })

  it('keeps the form open and displays an error when submission fails', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    mockSendFeedback.mockRejectedValue(new Error('network error'))
    renderFeedbackDialog({ onClose })

    fireEvent.change(screen.getByRole('textbox', { name: 'Description' }), {
      target: { value: 'Unable to load.' }
    })
    await user.click(screen.getByRole('button', { name: 'Send Feedback' }))

    expect(
      await screen.findByText("We couldn't send your feedback. Please check your connection and try again.")
    ).toBeInTheDocument()
    expect(onClose).not.toHaveBeenCalled()
  })

  it('closes without submitting when cancelled', () => {
    const onClose = vi.fn()
    renderFeedbackDialog({ onClose })

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onClose).toHaveBeenCalled()
    expect(mockSendFeedback).not.toHaveBeenCalled()
  })

  it('disables the form while offline', () => {
    renderFeedbackDialog({ isOnline: false })

    expect(screen.getByText('Feedback is unavailable while offline.')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Name' })).toBeDisabled()
    expect(screen.getByRole('textbox', { name: 'Email' })).toBeDisabled()
    expect(screen.getByRole('textbox', { name: 'Description' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Send Feedback' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeEnabled()
    expect(mockSendFeedback).not.toHaveBeenCalled()
  })
})
