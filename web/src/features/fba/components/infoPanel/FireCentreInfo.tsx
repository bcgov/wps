import React from 'react'
import { Accordion, AccordionSummary, AccordionDetails } from '@mui/material'
import { styled } from '@mui/material/styles'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import FireZoneUnitInfo from 'features/fba/components/FireZoneUnitInfo'
import { groupBy } from 'lodash'
import { FireShapeAreaDetail } from 'api/fbaAPI'

interface FireCentreInfoProps {
  advisoryThreshold: number
  fireCentreName: string
  fireZoneUnitInfos: FireShapeAreaDetail[]
}

const StyledAccordionSummary = styled(AccordionSummary)(() => ({
  flexDirection: 'row-reverse',
  fontSize: '0.85rem',
  fontWeight: 'bold',
  margin: '0px',
  minHeight: '32px',
  ['& . .MuiButtonBase-root.MuiAccordionSummary-root']: {
    minHeight: '32px'
  }
}))

const FireCenterInfo = ({ advisoryThreshold, fireCentreName, fireZoneUnitInfos }: FireCentreInfoProps) => {
  const groupedFireZoneUnitInfos = groupBy(fireZoneUnitInfos, 'fire_shape_name')
  return (
    <Accordion disableGutters defaultExpanded={false} elevation={0}>
      <StyledAccordionSummary expandIcon={<ExpandMoreIcon />}>{fireCentreName}</StyledAccordionSummary>
      <AccordionDetails sx={{ paddingTop: '0px', paddingBottom: '0px' }}>
        {Object.keys(groupedFireZoneUnitInfos).map((key, index) => {
          return (
            <FireZoneUnitInfo
              key={index}
              advisoryThreshold={advisoryThreshold}
              fireZoneUnitName={key}
              fireZoneUnitDetails={groupedFireZoneUnitInfos[key]}
            />
          )
        })}
      </AccordionDetails>
    </Accordion>
  )
}

export default FireCenterInfo
