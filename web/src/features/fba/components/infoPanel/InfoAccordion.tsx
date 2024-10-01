import React from 'react'

import { Accordion, AccordionDetails, AccordionSummary, Box, Typography } from '@mui/material'
import { styled, useTheme } from '@mui/material/styles'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { INFO_PANEL_CONTENT_BACKGROUND, INFO_PANEL_HEADER_BACKGROUND } from 'app/theme'
import { AdvisoryStatus } from '@/utils/constants'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_LINE } from '@/features/fba/components/map/featureStylers'

const getAdvisoryBarColour = (advisoryStatus: AdvisoryStatus) => {
  switch (advisoryStatus) {
    case AdvisoryStatus.WARNING:
      return ADVISORY_RED_LINE
    case AdvisoryStatus.ADVISORY:
      return ADVISORY_ORANGE_FILL
    default:
      return INFO_PANEL_CONTENT_BACKGROUND
  }
}
interface AdvisoryStatusBarProps {
  barColour: string
}

const AdvisoryStatusBar = ({ barColour }: AdvisoryStatusBarProps) => (
  <Box
    data-testid="advisory-status-bar"
    sx={{
      height: '10px',
      background: `repeating-linear-gradient(135deg, ${barColour}, ${barColour} 40px, white 40px, white 70px)`
    }}
  />
)

interface InfoAccordionProps {
  accordionDetailBackgroundColour?: string
  children: React.ReactNode
  defaultExpanded: boolean
  title: string
  advisoryStatus?: AdvisoryStatus
}

const StyledAccordionSummary = styled(AccordionSummary)(() => ({
  backgroundColor: INFO_PANEL_HEADER_BACKGROUND,
  ['& .MuiAccordionSummary-content']: {
    margin: 0
  }
}))

// A component for rendering the provided title and content in an accordion format in the info panel.
const InfoAccordion = ({
  accordionDetailBackgroundColour,
  children,
  defaultExpanded,
  title,
  advisoryStatus
}: InfoAccordionProps) => {
  const theme = useTheme()

  return (
    <Accordion data-testid="info-accordion" disableGutters defaultExpanded={defaultExpanded} elevation={0}>
      <Box>
        <StyledAccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography
            data-testid="info-accordion-title"
            sx={{
              color: theme.palette.primary.main,
              fontWeight: 'bold',
              paddingLeft: '1.25rem'
            }}
            variant="h6"
          >
            {title}
          </Typography>
        </StyledAccordionSummary>
        {advisoryStatus && (
          <AdvisoryStatusBar data-testid="advisory-status-bar" barColour={getAdvisoryBarColour(advisoryStatus)} />
        )}
      </Box>
      <AccordionDetails
        data-testid="info-accordion-details"
        sx={{
          backgroundColor: accordionDetailBackgroundColour,
          margin: '0px',
          padding: '0px'
        }}
      >
        {children}
      </AccordionDetails>
    </Accordion>
  )
}

export default InfoAccordion
