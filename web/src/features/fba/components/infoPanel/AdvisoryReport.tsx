import { useFireCentreDetails } from '@/features/fba/hooks/useFireCentreDetails'
import { Grid } from '@mui/material'
import { FireCenter, FireShape } from 'api/fbaAPI'
import { INFO_PANEL_CONTENT_BACKGROUND } from 'app/theme'
import AdvisoryText from 'features/fba/components/infoPanel/AdvisoryText'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { DateTime } from 'luxon'
import React from 'react'

interface AdvisoryReportProps {
  issueDate: DateTime | null
  forDate: DateTime
  selectedFireCenter?: FireCenter
  selectedFireZoneUnit?: FireShape
}

const AdvisoryReport = ({ issueDate, forDate, selectedFireCenter, selectedFireZoneUnit }: AdvisoryReportProps) => {
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
        advisoryStatus={fireZoneUnitDetails?.status}
      >
        <Grid container justifyContent="center">
          <Grid item sx={{ width: '90%' }}>
            <AdvisoryText
              issueDate={issueDate}
              forDate={forDate}
              selectedFireCenter={selectedFireCenter}
              selectedFireZoneUnit={selectedFireZoneUnit}
            ></AdvisoryText>
          </Grid>
        </Grid>
      </InfoAccordion>
    </div>
  )
}

export default AdvisoryReport
