import { getFeedback } from '@sentry/react'

const getFeedbackIntegration = () => getFeedback()

export const isFeedbackAvailable = () => Boolean(getFeedbackIntegration())

export const openFeedbackForm = async () => {
  const feedback = getFeedbackIntegration()
  if (!feedback) {
    return
  }

  const form = await feedback.createForm()
  form.appendToDom()
  form.open()
}
