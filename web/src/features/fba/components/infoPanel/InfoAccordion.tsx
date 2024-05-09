import React from 'react'

import { Accordion, AccordionDetails, AccordionSummary, Typography } from '@mui/material'
import { styled, useTheme } from '@mui/material/styles'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

interface InfoAccordionProps {
  children: React.ReactNode
  defaultExpanded: boolean
  title: string
}

const StyledAccordionSummary = styled(AccordionSummary)(() => ({
  backgroundColor: '#e4e4e5',
  ['& .MuiAccordionSummary-content']: {
    margin: 0
  }
}))

// A component for rendering the provided title and content in an accordion format in the info panel.
const InfoAccordion = ({ children, defaultExpanded, title }: InfoAccordionProps) => {
  const theme = useTheme()

  return (
    <Accordion data-testid="info-accordion" disableGutters defaultExpanded={defaultExpanded} elevation={0}>
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
      <AccordionDetails data-testid="info-accordion-details" sx={{ paddingTop: '0px', paddingBottom: '0px' }}>
        {children}
      </AccordionDetails>
    </Accordion>
  )
}

export default InfoAccordion
