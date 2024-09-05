import { Box, Grid, Tab, Tabs, Tooltip } from '@mui/material'
import { FireCenter, FireCentreHfiFuelsData, FireShape, FireShapeAreaDetail, FireZoneTPIStats } from 'api/fbaAPI'
import { INFO_PANEL_CONTENT_BACKGROUND, theme } from 'app/theme'
import FireZoneUnitSummary from 'features/fba/components/infoPanel/FireZoneUnitSummary'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import TabPanel from 'features/fba/components/infoPanel/TabPanel'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from 'features/fba/components/map/featureStylers'
import { useFireZoneUnitDetails } from 'features/fba/hooks/useFireZoneUnitDetails'
import { isNull, isUndefined } from 'lodash'
import React, { useEffect, useState } from 'react'

interface FireZoneUnitTabs {
  selectedFireZoneUnit: FireShape | undefined
  setZoomSource: React.Dispatch<React.SetStateAction<'fireCenter' | 'fireShape' | undefined>>
  fireCentreTPIStats: Record<string, FireZoneTPIStats[]> | null
  fireCentreHfiFuelTypes: FireCentreHfiFuelsData
  selectedFireCenter: FireCenter | undefined
  advisoryThreshold: number
  setSelectedFireShape: React.Dispatch<React.SetStateAction<FireShape | undefined>>
}

const calculateStatus = (details: FireShapeAreaDetail[], advisoryThreshold: number) => {
  let status = '#DCDCDC'

  if (details.length === 0) {
    return status
  }

  const advisoryThresholdDetail = details.find(detail => detail.threshold == 1)
  const warningThresholdDetail = details.find(detail => detail.threshold == 2)
  const advisoryPercentage = advisoryThresholdDetail?.elevated_hfi_percentage ?? 0
  const warningPercentage = warningThresholdDetail?.elevated_hfi_percentage ?? 0

  if (advisoryPercentage + warningPercentage > advisoryThreshold) {
    status = ADVISORY_ORANGE_FILL
  }

  if (warningPercentage > advisoryThreshold) {
    status = ADVISORY_RED_FILL
  }

  return status
}

const FireZoneUnitTabs = ({
  selectedFireZoneUnit,
  setZoomSource,
  selectedFireCenter,
  advisoryThreshold,
  fireCentreTPIStats,
  fireCentreHfiFuelTypes,
  setSelectedFireShape
}: FireZoneUnitTabs) => {
  const [tabNumber, setTabNumber] = useState(0)

  const sortedGroupedFireZoneUnits = useFireZoneUnitDetails(selectedFireCenter)

  useEffect(() => {
    if (selectedFireZoneUnit) {
      const newIndex = sortedGroupedFireZoneUnits.findIndex(
        zone => zone.fire_shape_id === selectedFireZoneUnit.fire_shape_id
      )
      if (newIndex !== -1) {
        setTabNumber(newIndex)
      }
    } else {
      setTabNumber(0)
      setSelectedFireShape(getTabFireShape(0))
    }
  }, [selectedFireZoneUnit, sortedGroupedFireZoneUnits])

  const getTabFireShape = (tabNumber: number): FireShape | undefined => {
    if (sortedGroupedFireZoneUnits.length > 0) {
      const selectedTabZone = sortedGroupedFireZoneUnits[tabNumber]

      const fireShape: FireShape = {
        fire_shape_id: selectedTabZone.fire_shape_id,
        mof_fire_centre_name: selectedTabZone.fire_centre_name,
        mof_fire_zone_name: selectedTabZone.fire_shape_name
      }

      return fireShape
    }
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabNumber(newValue)

    const fireShape = getTabFireShape(newValue)
    setSelectedFireShape(fireShape)
    setZoomSource('fireShape')
  }

  if (isUndefined(selectedFireCenter) || isNull(selectedFireCenter)) {
    return <div data-testid="fire-zone-unit-summary-empty"></div>
  }

  const tpiStatsArray = fireCentreTPIStats?.[selectedFireCenter.name]
  const hfiFuelStats = fireCentreHfiFuelTypes?.[selectedFireCenter.name]

  return (
    <div data-testid="firezone-summary-tabs">
      <InfoAccordion
        defaultExpanded={true}
        title={selectedFireCenter.name}
        accordionDetailBackgroundColour={INFO_PANEL_CONTENT_BACKGROUND}
      >
        <Grid container justifyContent="center" minHeight={500}>
          <Grid item sx={{ width: '95%' }}>
            <Box>
              <Tabs
                value={tabNumber}
                onChange={handleTabChange}
                sx={{
                  '.MuiTabs-indicator': {
                    height: '4px'
                  }
                }}
              >
                {sortedGroupedFireZoneUnits.map((zone, index) => {
                  const isActive = tabNumber === index
                  const key = zone.fire_shape_id
                  return (
                    <Tooltip key={key} title={zone.fire_shape_name} placement="top-start" arrow>
                      <Tab
                        key={key}
                        sx={{
                          backgroundColor: calculateStatus(zone.fireShapeDetails, advisoryThreshold),
                          minWidth: 'auto',
                          //   border: '0.25px solid grey',
                          marginTop: theme.spacing(2),
                          fontWeight: 'bold',
                          color: isActive ? 'black' : 'grey',
                          minHeight: '30px'
                        }}
                        label={zone.fire_shape_name.split('-')[0]}
                      />
                    </Tooltip>
                  )
                })}
              </Tabs>
            </Box>
            {sortedGroupedFireZoneUnits.map((zone, index) => (
              <TabPanel key={zone.fire_shape_id} value={tabNumber} index={index}>
                <FireZoneUnitSummary
                  fuelTypeInfo={hfiFuelStats ? { [zone.fire_shape_id]: hfiFuelStats[zone.fire_shape_id] } : {}}
                  fireZoneTPIStats={
                    tpiStatsArray ? tpiStatsArray.find(stats => stats.fire_zone_id == zone.fire_shape_id) : undefined
                  }
                  selectedFireZoneUnit={selectedFireZoneUnit}
                />
              </TabPanel>
            ))}
          </Grid>
        </Grid>
      </InfoAccordion>
    </div>
  )
}

export default FireZoneUnitTabs
