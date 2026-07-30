import { sendFeedback } from '@sentry/react'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { FeedbackDialog } from '@/components/FeedbackDialog'

vi.mock('@sentry/react', () => ({
  sendFeedback: vi.fn()
}))

const mockSendFeedback = vi.mocked(sendFeedback)

describe('FeedbackDialog', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('prefills the authenticated email and keeps close controls available', () => {
    render(<FeedbackDialog defaultEmail="user@example.com" isOnline onClose={vi.fn()} open />)

    expect(screen.getByRole('textbox', { name: 'Email' })).toHaveValue('user@example.com')
    expect(screen.getByRole('button', { name: 'close feedback' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })

  it('keeps the description label above the outline when focus changes', () => {
    render(<FeedbackDialog isOnline onClose={vi.fn()} open />)
    const description = screen.getByRole('textbox', { name: 'Description' })
    const label = document.querySelector(`label[for="${description.id}"]`)

    expect(label).toHaveAttribute('data-shrink', 'true')
    fireEvent.focus(description)
    expect(label).toHaveAttribute('data-shrink', 'true')
    fireEvent.blur(description)
    expect(label).toHaveAttribute('data-shrink', 'true')
    fireEvent.focus(description)
    expect(label).toHaveAttribute('data-shrink', 'true')
  })

  it('sends feedback through Sentry and closes the form', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    mockSendFeedback.mockResolvedValue('event-id')
    render(<FeedbackDialog defaultEmail="user@example.com" isOnline onClose={onClose} open />)

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
    render(<FeedbackDialog isOnline onClose={onClose} open />)

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
    render(<FeedbackDialog isOnline onClose={onClose} open />)

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onClose).toHaveBeenCalled()
    expect(mockSendFeedback).not.toHaveBeenCalled()
  })

  it('disables the form while offline', () => {
    render(<FeedbackDialog isOnline={false} onClose={vi.fn()} open />)

    expect(screen.getByText('Feedback is unavailable while offline.')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Name' })).toBeDisabled()
    expect(screen.getByRole('textbox', { name: 'Email' })).toBeDisabled()
    expect(screen.getByRole('textbox', { name: 'Description' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Send Feedback' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeEnabled()
    expect(mockSendFeedback).not.toHaveBeenCalled()
  })
})
