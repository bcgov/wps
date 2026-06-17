import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import FeedbackButton from './FeedbackButton'

vi.mock('@sentry/react', () => ({
  getFeedback: vi.fn()
}))

import { getFeedback } from '@sentry/react'

const mockGetFeedback = getFeedback as ReturnType<typeof vi.fn>

describe('FeedbackButton', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders nothing when getFeedback returns undefined', () => {
    mockGetFeedback.mockReturnValue(undefined)
    const { container } = render(<FeedbackButton color="primary" />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders the button when getFeedback returns an integration', () => {
    const mockForm = {
      appendToDom: vi.fn(),
      open: vi.fn()
    }
    mockGetFeedback.mockReturnValue({
      createForm: vi.fn().mockResolvedValue(mockForm)
    })
    render(<FeedbackButton color="primary" />)
    expect(screen.getByRole('button', { name: /submit feedback/i })).toBeInTheDocument()
  })

  it('opens the feedback form when button is clicked', async () => {
    const mockForm = {
      appendToDom: vi.fn(),
      open: vi.fn()
    }
    const mockCreateForm = vi.fn().mockResolvedValue(mockForm)
    mockGetFeedback.mockReturnValue({ createForm: mockCreateForm })

    render(<FeedbackButton color="primary" />)
    fireEvent.click(screen.getByRole('button', { name: /submit feedback/i }))

    await waitFor(() => {
      expect(mockCreateForm).toHaveBeenCalled()
      expect(mockForm.appendToDom).toHaveBeenCalled()
      expect(mockForm.open).toHaveBeenCalled()
    })
  })
})
