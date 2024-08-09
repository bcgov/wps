import React from 'react'
import { Accordion, AccordionSummary, AccordionDetails } from '@mui/material'
import { styled, useTheme } from '@mui/material/styles'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import FireZoneUnitInfo from 'features/fba/components/infoPanel/FireZoneUnitInfo'
import { groupBy } from 'lodash'
import { FireShapeAreaDetail } from 'api/fbaAPI'
import { INFO_PANEL_CONTENT_BACKGROUND } from 'app/theme'

interface FireCentreInfoProps {
  advisoryThreshold: number
  expanded: boolean
  fireCentreName: string
  fireZoneUnitInfos: FireShapeAreaDetail[]
  onChangeExpanded: (name: string) => (event: React.SyntheticEvent, isExpanded: boolean) => void
}

const StyledAccordionSummary = styled(AccordionSummary)(({ theme }) => ({
  backgroundColor: INFO_PANEL_CONTENT_BACKGROUND,
  flexDirection: 'row-reverse',
  fontWeight: 'bold',
  margin: '0px',
  minHeight: theme.spacing(4),
  ['& . .MuiButtonBase-root.MuiAccordionSummary-root']: {
    minHeight: theme.spacing(4)
  }
}))

const FireCenterInfo = ({
  advisoryThreshold,
  expanded,
  fireCentreName,
  fireZoneUnitInfos,
  onChangeExpanded
}: FireCentreInfoProps) => {
  const theme = useTheme()
  const groupedFireZoneUnitInfos = groupBy(fireZoneUnitInfos, 'fire_shape_name')
  return (
    <Accordion
      data-testid={`fire-centre-info`}
      disableGutters
      expanded={expanded}
      elevation={0}
      onChange={onChangeExpanded(fireCentreName)}
      sx={{ marginLeft: theme.spacing(2) }}
    >
      <StyledAccordionSummary expandIcon={<ExpandMoreIcon />}>{fireCentreName}</StyledAccordionSummary>
      <AccordionDetails
        sx={{
          backgroundColor: INFO_PANEL_CONTENT_BACKGROUND,
          padding: '0',
          paddingLeft: theme.spacing(2),
          paddingRight: theme.spacing(2)
        }}
      >
        {Object.keys(groupedFireZoneUnitInfos)
          .sort((a, b) => a.localeCompare(b))
          .map(key => {
            return (
              <FireZoneUnitInfo
                key={key}
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
