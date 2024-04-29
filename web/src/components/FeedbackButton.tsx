import React from 'react'
import { Button } from '@mui/material'
import CampaignIcon from '@mui/icons-material/Campaign'
import { feedbackIntegration } from '@sentry/react'

const FeedbackButton = ({ color }: { color: 'primary' | 'inherit' }) => {
  const feedback = feedbackIntegration({ colorScheme: 'system' })

  if (!feedback) {
    return null
  }

  return (
    <Button startIcon={<CampaignIcon />} variant={'contained'} color={color} onClick={() => feedback.openDialog()}>
      Submit Feedback
    </Button>
  )
}

export default React.memo(FeedbackButton)
