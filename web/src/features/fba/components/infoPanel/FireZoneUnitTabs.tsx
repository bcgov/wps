import { Box, Grid, Tab, Tabs, Tooltip } from '@mui/material'
import { FireCenter, FireShape, FireShapeAreaDetail, FireZoneThresholdFuelTypeArea, FireZoneTPIStats } from 'api/fbaAPI'
import { INFO_PANEL_CONTENT_BACKGROUND, theme, TRANSPARENT_COLOUR } from 'app/theme'
import FireZoneUnitSummary from 'features/fba/components/infoPanel/FireZoneUnitSummary'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import TabPanel from 'features/fba/components/infoPanel/TabPanel'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from 'features/fba/components/map/featureStylers'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import { groupBy, isNull, isUndefined } from 'lodash'
import React, { useEffect, useMemo, useState } from 'react'
import { useSelector } from 'react-redux'

interface FireZoneUnitTabs {
  selectedFireZoneUnit: FireShape | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
  fireZoneTPIStats: FireZoneTPIStats | null
  selectedFireCenter: FireCenter | undefined
  advisoryThreshold: number
  setSelectedFireShape: React.Dispatch<React.SetStateAction<FireShape | undefined>>
}

const calculateStatus = (details: FireShapeAreaDetail[], advisoryThreshold: number) => {
  let status = 'white'

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
  fuelTypeInfo,
  fireZoneTPIStats,
  selectedFireZoneUnit,
  selectedFireCenter,
  advisoryThreshold,
  setSelectedFireShape
}: FireZoneUnitTabs) => {
  const provincialSummary = useSelector(selectProvincialSummary)
  const [tabNumber, setTabNumber] = useState(0)

  const fireCenterSummary = selectedFireCenter ? provincialSummary[selectedFireCenter.name] : []
  const groupedFireZoneUnitInfos = useMemo(() => groupBy(fireCenterSummary, 'fire_shape_name'), [fireCenterSummary])
  const sortedZoneNames = useMemo(() => Object.keys(groupedFireZoneUnitInfos).sort(), [groupedFireZoneUnitInfos])

  useEffect(() => {
    if (selectedFireZoneUnit) {
      const newIndex = sortedZoneNames.indexOf(selectedFireZoneUnit.mof_fire_zone_name)
      if (newIndex !== -1) {
        setTabNumber(newIndex)
      }
    } else {
      setTabNumber(0)
      setSelectedFireShape(getTabFireShape(0))
    }
  }, [selectedFireZoneUnit, selectedFireCenter])

  const getTabFireShape = (tabNumber: number): FireShape | undefined => {
    if (sortedZoneNames.length > 0) {
      const selectedTabZone = sortedZoneNames[tabNumber]
      const selectedFireShapeInfo = groupedFireZoneUnitInfos[selectedTabZone][0]

      const fireShape: FireShape = {
        fire_shape_id: selectedFireShapeInfo.fire_shape_id,
        mof_fire_centre_name: selectedFireShapeInfo.fire_centre_name,
        mof_fire_zone_name: selectedFireShapeInfo.fire_shape_name
      }

      return fireShape
    }
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabNumber(newValue)

    const fireShape = getTabFireShape(newValue)
    setSelectedFireShape(fireShape)
  }

  if (isUndefined(selectedFireCenter) || isNull(selectedFireCenter)) {
    return <div data-testid="fire-zone-unit-summary-empty"></div>
  }

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
              <Tabs value={tabNumber} onChange={handleTabChange}>
                {sortedZoneNames.map((key, index) => {
                  const isActive = tabNumber === index
                  return (
                    <Tooltip title={key} placement="top-start" arrow>
                      <Tab
                        key={key}
                        sx={{
                          backgroundColor: calculateStatus(groupedFireZoneUnitInfos[key], advisoryThreshold),
                          minWidth: 'auto',
                          borderTopLeftRadius: '4px',
                          borderTopRightRadius: '4px',
                          border: '1px solid grey',
                          marginRight: '4px',
                          marginTop: theme.spacing(2),
                          fontWeight: 'bold',
                          color: isActive ? 'black' : 'grey',
                          minHeight: '30px'
                        }}
                        label={key.split('-')[0]}
                      />
                    </Tooltip>
                  )
                })}
              </Tabs>
            </Box>
            {sortedZoneNames.map((key, index) => (
              <TabPanel key={key} value={tabNumber} index={index}>
                <FireZoneUnitSummary
                  fuelTypeInfo={fuelTypeInfo}
                  fireZoneTPIStats={fireZoneTPIStats}
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
