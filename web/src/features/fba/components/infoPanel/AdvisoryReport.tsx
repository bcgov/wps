import { calculateStatusText } from '@/features/fba/calculateZoneStatus'
import { useFireCentreDetails } from '@/features/fba/hooks/useFireCentreDetails'
import { Box, Tabs, Tab, Grid } from '@mui/material'
import { FireCenter, FireShape } from 'api/fbaAPI'
import { INFO_PANEL_CONTENT_BACKGROUND } from 'app/theme'
import AdvisoryText from 'features/fba/components/infoPanel/AdvisoryText'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { DateTime } from 'luxon'
import React, { useState } from 'react'

interface AdvisoryReportProps {
  issueDate: DateTime | null
  forDate: DateTime
  advisoryThreshold: number
  selectedFireCenter?: FireCenter
  selectedFireZoneUnit?: FireShape
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel = ({ children, index, value }: TabPanelProps) => {
  return (
    <div hidden={value !== index} id={`tabpanel-${index}`} data-testid={`tabpanel-${index}`}>
      {value === index && <Box paddingBottom={3}>{children}</Box>}
    </div>
  )
}

const AdvisoryReport = ({
  issueDate,
  forDate,
  advisoryThreshold,
  selectedFireCenter,
  selectedFireZoneUnit
}: AdvisoryReportProps) => {
  const [tabNumber, setTabNumber] = useState(0)

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabNumber(newValue)
  }

  const groupedFireZoneUnits = useFireCentreDetails(selectedFireCenter)
  const fireZoneUnitDetails = groupedFireZoneUnits.find(
    zone => zone.fire_shape_id === selectedFireZoneUnit?.fire_shape_id
  )

  return (
    <div data-testid="advisory-report">
      <InfoAccordion
        defaultExpanded={true}
        title={'Advisory Report'}
        accordionDetailBackgroundColour={INFO_PANEL_CONTENT_BACKGROUND}
        showAdvisoryStatusBar={true}
        advisoryStatus={calculateStatusText(fireZoneUnitDetails?.fireShapeDetails || [], advisoryThreshold)}
      >
        <Grid container justifyContent="center">
          <Grid item sx={{ width: '90%' }}>
            <Box>
              <Tabs value={tabNumber} onChange={handleTabChange}>
                <Tab aria-label="bulletin" label="BULLETIN" />
              </Tabs>
            </Box>
            <TabPanel value={tabNumber} index={0}>
              <AdvisoryText
                issueDate={issueDate}
                forDate={forDate}
                advisoryThreshold={advisoryThreshold}
                selectedFireCenter={selectedFireCenter}
                selectedFireZoneUnit={selectedFireZoneUnit}
              ></AdvisoryText>
            </TabPanel>
          </Grid>
        </Grid>
      </InfoAccordion>
    </div>
  )
}

export default AdvisoryReport
