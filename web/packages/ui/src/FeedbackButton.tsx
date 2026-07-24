import CampaignIcon from '@mui/icons-material/Campaign'
import { Button } from '@mui/material'
import React from 'react'
import { isFeedbackAvailable, openFeedbackForm } from './openFeedbackForm'

const FeedbackButton = ({ color }: { color: 'primary' | 'inherit' }) => {
  if (!isFeedbackAvailable()) {
    return null
  }

  return (
    <Button startIcon={<CampaignIcon />} variant={'contained'} color={color} onClick={openFeedbackForm}>
      Submit Feedback
    </Button>
  )
}

export default React.memo(FeedbackButton)
