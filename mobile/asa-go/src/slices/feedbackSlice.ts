import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { sendFeedback } from '@sentry/react'
import type { AppThunk } from '@/store'

interface FeedbackSubmission {
  email?: string
  message: string
  name?: string
}

interface FeedbackState {
  activeSubmissionId: number | null
  error: string | null
  isSubmitting: boolean
  submitted: boolean
}

interface SubmissionFailedPayload {
  error: string
  submissionId: number
}

export const feedbackInitialState: FeedbackState = {
  activeSubmissionId: null,
  error: null,
  isSubmitting: false,
  submitted: false
}

const feedbackSlice = createSlice({
  name: 'feedback',
  initialState: feedbackInitialState,
  reducers: {
    feedbackSubmissionStarted(state, action: PayloadAction<number>) {
      state.activeSubmissionId = action.payload
      state.error = null
      state.isSubmitting = true
      state.submitted = false
    },
    feedbackSubmissionSucceeded(state, action: PayloadAction<number>) {
      if (state.activeSubmissionId !== action.payload) {
        return
      }
      state.activeSubmissionId = null
      state.isSubmitting = false
      state.submitted = true
    },
    feedbackSubmissionFailed(state, action: PayloadAction<SubmissionFailedPayload>) {
      if (state.activeSubmissionId !== action.payload.submissionId) {
        return
      }
      state.activeSubmissionId = null
      state.error = action.payload.error
      state.isSubmitting = false
      state.submitted = false
    },
    resetFeedbackSubmission() {
      return { ...feedbackInitialState }
    },
    setFeedbackError(state, action: PayloadAction<string | null>) {
      state.error = action.payload
    }
  }
})

export const {
  feedbackSubmissionFailed,
  feedbackSubmissionStarted,
  feedbackSubmissionSucceeded,
  resetFeedbackSubmission,
  setFeedbackError
} = feedbackSlice.actions

export default feedbackSlice.reducer

let nextSubmissionId = 0

export const submitFeedback =
  (feedback: FeedbackSubmission): AppThunk =>
  async dispatch => {
    const submissionId = ++nextSubmissionId
    dispatch(feedbackSubmissionStarted(submissionId))
    try {
      await sendFeedback(feedback, { includeReplay: true })
      dispatch(feedbackSubmissionSucceeded(submissionId))
    } catch {
      dispatch(
        feedbackSubmissionFailed({
          submissionId,
          error: "We couldn't send your feedback. Please check your connection and try again."
        })
      )
    }
  }
