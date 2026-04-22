import { useFireCentreDetails } from '@/features/fba/hooks/useFireCentreDetails'
import { Grid } from '@mui/material'
import { FireShape } from '@wps/api/fbaAPI'
import type { FireCentre } from '@wps/types/fireCentre'
import { INFO_PANEL_CONTENT_BACKGROUND } from '@wps/ui/theme'
import AdvisoryText from 'features/fba/components/infoPanel/AdvisoryText'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { DateTime } from 'luxon'

interface AdvisoryReportProps {
  issueDate: DateTime | null
  forDate: DateTime
  selectedFireCentre?: FireCentre
  selectedFireZoneUnit?: FireShape
}

const AdvisoryReport = ({ issueDate, forDate, selectedFireCentre, selectedFireZoneUnit }: AdvisoryReportProps) => {
  const groupedFireZoneUnits = useFireCentreDetails(selectedFireCentre)
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
          <Grid sx={{ width: '90%' }}>
            <AdvisoryText
              issueDate={issueDate}
              forDate={forDate}
              selectedFireCentre={selectedFireCentre}
              selectedFireZoneUnit={selectedFireZoneUnit}
            ></AdvisoryText>
          </Grid>
        </Grid>
      </InfoAccordion>
    </div>
  )
}

export default AdvisoryReport
