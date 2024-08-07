import { Box, Tabs, Tab, Grid, Typography } from '@mui/material'
import { FireShape, FireShapeArea } from 'api/fbaAPI'
import { INFO_PANEL_CONTENT_BACKGROUND } from 'app/theme'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { DateTime } from 'luxon'
import React, { useState } from 'react'

interface AdvisoryReportProps {
  issueDate: DateTime | null
  forDate: DateTime
  selectedFireZoneUnit: FireShape | undefined
  fireShapeAreas: FireShapeArea[]
  advisoryThreshold: number
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel = ({ children, index, value }: TabPanelProps) => {
  return (
    <div hidden={value !== index} id={`tabpanel-${index}`}>
      {value === index && <Box paddingBottom={3}>{children}</Box>}
    </div>
  )
}

const AdvisoryReport = ({
  issueDate,
  forDate,
  selectedFireZoneUnit,
  fireShapeAreas,
  advisoryThreshold
}: AdvisoryReportProps) => {
  const [value, setValue] = useState(0)

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue)
  }

  const calculateStatus = (details: FireShapeArea[]): string | undefined => {
    const advisoryThresholdDetail = details.find(detail => detail.threshold == 1)
    const warningThresholdDetail = details.find(detail => detail.threshold == 2)
    const advisoryPercentage = advisoryThresholdDetail?.elevated_hfi_percentage ?? 0
    const warningPercentage = warningThresholdDetail?.elevated_hfi_percentage ?? 0

    if (warningPercentage > advisoryThreshold) {
      return 'Warning'
    }

    if (advisoryPercentage + warningPercentage > advisoryThreshold) {
      return 'Advisory'
    }

    return
  }

  const composeAdvisoryText = (
    issueDate: DateTime | null,
    forDate: DateTime,
    selectedFireZoneUnit: FireShape | undefined,
    fireShapeAreas: FireShapeArea[]
  ) => {
    if (!issueDate?.isValid) {
      return {
        body: 'No advisories issued for today.',
        zones: []
      }
    }
    if (issueDate?.isValid && selectedFireZoneUnit) {
      const zoneDetails = fireShapeAreas.filter(area => area.fire_shape_id == selectedFireZoneUnit?.fire_shape_id)
      const zoneStatus = calculateStatus(zoneDetails)
      const forToday = issueDate.toISODate() === forDate.toISODate()
      const displayForDate = forToday ? 'today' : forDate.toISODate()

      if (!zoneStatus) {
        return {
          body: `No advisory/warning issued for the selected zone.`,
          zones: []
        }
      }

      return {
        body:
          `Issued on ${issueDate.toLocaleString(DateTime.DATE_MED)} for ${displayForDate}. \n\n` +
          `There is a fire behaviour ${zoneStatus} in effect in the following areas:`,
        zones: [selectedFireZoneUnit.mof_fire_zone_name]
      }
    } else {
      return {
        body: `No fire zone selected.`,
        zones: []
      }
    }
  }

  const advisoryText = composeAdvisoryText(issueDate, forDate, selectedFireZoneUnit, fireShapeAreas)

  return (
    <div data-testid="advisory-report">
      <InfoAccordion
        defaultExpanded={true}
        title={'Advisory Report'}
        accordionDetailBackgroundColour={INFO_PANEL_CONTENT_BACKGROUND}
      >
        <Grid container justifyContent="center">
          <Grid item sx={{ width: '90%' }}>
            <Box>
              <Tabs value={value} onChange={handleTabChange}>
                <Tab label="BULLETIN" />
              </Tabs>
            </Box>
            <TabPanel value={value} index={0}>
              <Box
                sx={{
                  height: 300,
                  maxWidth: '100%',
                  overflow: 'auto',
                  border: '1px solid #ccc',
                  padding: 2,
                  borderRadius: 1,
                  backgroundColor: 'white'
                }}
              >
                <Typography sx={{ whiteSpace: 'pre-wrap' }}>{advisoryText.body}</Typography>
                {advisoryText.zones.length > 0 && (
                  <ul>
                    {advisoryText.zones.map((zone, index) => (
                      <li key={index}>
                        <Typography>{zone}</Typography>
                      </li>
                    ))}
                  </ul>
                )}
              </Box>
            </TabPanel>
          </Grid>
        </Grid>
      </InfoAccordion>
    </div>
  )
}

export default AdvisoryReport
