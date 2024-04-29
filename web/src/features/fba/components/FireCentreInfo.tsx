import React from 'react'
import { Accordion, AccordionSummary, AccordionDetails } from '@mui/material'
import { styled } from '@mui/material/styles'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import FireZoneUnitInfo from 'features/fba/components/FireZoneUnitInfo'

export interface FireZoneUnitStatus {
  fireZoneUnitName: string
  status: 0 | 1 | 2
}

export interface FireZoneCentreInfo {
  fireCentreName: string
  fireZoneUnits: FireZoneUnitStatus[]
}

interface FireCentreInfoProps {
  fireCentreName: string
  fireZoneUnits: FireZoneUnitStatus[]
}

const StyledAccordionSummary = styled(AccordionSummary)(() => ({
  flexDirection: 'row-reverse',
  fontSize: '0.85rem',
  fontWeight: 'bold',
  minHeight: '32px',
  ['& . .MuiButtonBase-root.MuiAccordionSummary-root']: {
    minHeight: '32px'
  },
  ['& .MuiAccordionSummary-content.Mui-expanded']: {
    margin: '0px'
  }
}))

const StyledAccordion = styled(Accordion)(() => ({
  ['& .MuiPaper-root .MuiAccordion-root .MuiAccordion-rounded .Mui-expanded']: {
    margin: '0px'
  }
}))

const FireCenterInfo = ({ fireCentreName, fireZoneUnits }: FireCentreInfoProps) => {
  return (
    <Accordion disableGutters defaultExpanded={true} elevation={0}>
      <StyledAccordionSummary expandIcon={<ExpandMoreIcon />}>{fireCentreName}</StyledAccordionSummary>
      <AccordionDetails sx={{ paddingTop: '0px', paddingBottom: '0px' }}>
        {fireZoneUnits.map(unit => {
          return (
            <FireZoneUnitInfo
              key={unit.fireZoneUnitName}
              fireZoneUnitName={unit.fireZoneUnitName}
              status={unit.status}
            ></FireZoneUnitInfo>
          )
        })}
      </AccordionDetails>
    </Accordion>
  )
}

export default FireCenterInfo
