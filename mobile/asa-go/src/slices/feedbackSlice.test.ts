import reducer, {
  feedbackInitialState,
  feedbackSubmissionFailed,
  feedbackSubmissionStarted,
  feedbackSubmissionSucceeded,
  resetFeedbackSubmission
} from '@/slices/feedbackSlice'

describe('feedbackSlice', () => {
  it('tracks a successful submission', () => {
    const submittingState = reducer(feedbackInitialState, feedbackSubmissionStarted(1))

    expect(submittingState).toEqual({
      activeSubmissionId: 1,
      error: null,
      isSubmitting: true,
      submitted: false
    })
    expect(reducer(submittingState, feedbackSubmissionSucceeded(1))).toEqual({
      activeSubmissionId: null,
      error: null,
      isSubmitting: false,
      submitted: true
    })
  })

  it('stores an error for a failed submission', () => {
    const submittingState = reducer(feedbackInitialState, feedbackSubmissionStarted(1))

    expect(
      reducer(submittingState, feedbackSubmissionFailed({ error: 'Unable to send feedback.', submissionId: 1 }))
    ).toEqual({
      activeSubmissionId: null,
      error: 'Unable to send feedback.',
      isSubmitting: false,
      submitted: false
    })
  })

  it('ignores a submission result after the flow is reset', () => {
    const submittingState = reducer(feedbackInitialState, feedbackSubmissionStarted(1))
    const resetState = reducer(submittingState, resetFeedbackSubmission())

    expect(reducer(resetState, feedbackSubmissionSucceeded(1))).toEqual(feedbackInitialState)
    expect(
      reducer(resetState, feedbackSubmissionFailed({ error: 'Unable to send feedback.', submissionId: 1 }))
    ).toEqual(feedbackInitialState)
  })
})
