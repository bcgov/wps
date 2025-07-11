import { selectFireCentreHFIFuelStats, selectFireCentreTPIStats } from '@/app/rootReducer'
import { calculateStatusColour } from '@/features/fba/calculateZoneStatus'
import { useFilteredFireCentreHFIFuelStats } from '@/features/fba/hooks/useFilteredFireCentreHFIFuelStats'
import { Box, Grid, Tab, Tabs, Tooltip, Typography } from '@mui/material'
import { FireCenter, FireShape } from 'api/fbaAPI'
import { INFO_PANEL_CONTENT_BACKGROUND, theme } from 'app/theme'
import FireZoneUnitSummary from 'features/fba/components/infoPanel/FireZoneUnitSummary'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import TabPanel from 'features/fba/components/infoPanel/TabPanel'
import { useFireCentreDetails } from 'features/fba/hooks/useFireCentreDetails'
import { isEmpty, isNil, isNull, isUndefined } from 'lodash'
import React, { useEffect, useMemo, useState } from 'react'
import { useSelector } from 'react-redux'

interface FireZoneUnitTabs {
  selectedFireZoneUnit: FireShape | undefined
  setZoomSource: React.Dispatch<React.SetStateAction<'fireCenter' | 'fireShape' | undefined>>
  selectedFireCenter: FireCenter | undefined
  advisoryThreshold: number
  setSelectedFireShape: React.Dispatch<React.SetStateAction<FireShape | undefined>>
}

const FireZoneUnitTabs = ({
  selectedFireZoneUnit,
  setZoomSource,
  selectedFireCenter,
  advisoryThreshold,
  setSelectedFireShape
}: FireZoneUnitTabs) => {
  const { fireCentreTPIStats } = useSelector(selectFireCentreTPIStats)
  const [tabNumber, setTabNumber] = useState(0)

  const sortedGroupedFireZoneUnits = useFireCentreDetails(selectedFireCenter)
  const filteredFireCentreHFIFuelStats = useFilteredFireCentreHFIFuelStats()

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
      setSelectedFireShape(getTabFireShape(0)) // if no selected FireShape, select the first one in the sorted tabs
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

  const tpiStatsArray = useMemo(() => {
    if (selectedFireCenter && !isNil(fireCentreTPIStats)) {
      return fireCentreTPIStats?.firezone_tpi_stats
    }
  }, [fireCentreTPIStats, selectedFireCenter])

  const hfiFuelStats = useMemo(() => {
    if (selectedFireCenter) {
      return filteredFireCentreHFIFuelStats?.[selectedFireCenter?.name]
    }
  }, [filteredFireCentreHFIFuelStats, selectedFireCenter])

  if (isUndefined(selectedFireCenter) || isNull(selectedFireCenter)) {
    return <div data-testid="fire-zone-unit-tabs-empty"></div>
  }

  return (
    <div data-testid="firezone-summary-tabs">
      <InfoAccordion
        defaultExpanded={true}
        title={selectedFireCenter.name}
        accordionDetailBackgroundColour={INFO_PANEL_CONTENT_BACKGROUND}
      >
        {isEmpty(sortedGroupedFireZoneUnits) && (
          <Typography sx={{ paddingLeft: '1rem', paddingTop: '1rem' }}>
            No advisory data available for the selected date.
          </Typography>
        )}
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
                        data-testid={`zone-${key}-tab`}
                        sx={{
                          backgroundColor: calculateStatusColour(zone.fireShapeDetails, advisoryThreshold, '#FFFFFF'),
                          minWidth: 'auto',
                          marginTop: theme.spacing(2),
                          fontWeight: 'bold',
                          color: isActive ? 'black' : 'grey',
                          minHeight: '30px'
                        }}
                        label={zone.fire_shape_name.split('-')[0]}
                        aria-label={`zone-${key}-tab`}
                      />
                    </Tooltip>
                  )
                })}
              </Tabs>
            </Box>
            {sortedGroupedFireZoneUnits.map((zone, index) => (
              <TabPanel key={zone.fire_shape_id} value={tabNumber} index={index}>
                <Typography
                  data-testid="fire-zone-title-tabs"
                  sx={{
                    color: '#003366',
                    fontWeight: 'bold',
                    textAlign: 'left',
                    paddingLeft: theme.spacing(2)
                  }}
                >
                  {zone.fire_shape_name}
                </Typography>
                <FireZoneUnitSummary
                  fireZoneFuelStats={
                    hfiFuelStats ? { [zone.fire_shape_id]: hfiFuelStats[zone.fire_shape_id].fuel_area_stats } : {}
                  }
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
