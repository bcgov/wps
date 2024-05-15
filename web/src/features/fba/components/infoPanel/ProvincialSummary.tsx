import React, { useState } from 'react'
import { useSelector } from 'react-redux'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import FireCentreInfo from 'features/fba/components/infoPanel/FireCentreInfo'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { isNull, isUndefined } from 'lodash'
import { Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { INFO_PANEL_CONTENT_BACKGORUND } from 'app/theme'
import { CARIBOO_FC, COASTAL_FC, KAMLOOPS_FC, NORTHWEST_FC, PRINCE_GEORGE_FC, SOUTHEAST_FC } from 'utils/constants'

interface ProvincialSummaryProps {
  advisoryThreshold: number
}

export const NO_DATA_MESSAGE = 'Choose a date of interest above.'

// Displays advisory status of all fire zone units in all fire centres across BC.
const ProvincialSummary = ({ advisoryThreshold }: ProvincialSummaryProps) => {
  const [fireCentreExpanded, setFireCentreExpanded] = useState<Record<string, boolean>>({
    CARIBOO_FC: false,
    COASTAL_FC: true,
    KAMLOOPS_FC: false,
    NORTHWEST_FC: false,
    PRINCE_GEORGE_FC: false,
    SOUTHEAST_FC: false
  })
  const provincialSummary = useSelector(selectProvincialSummary)
  const theme = useTheme()
  const noProvincialSummary =
    isNull(provincialSummary) || isUndefined(provincialSummary) || Object.keys(provincialSummary).length === 0

  const handleFireCentreAccordionChanged =
    (fireCenterName: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
      const newValue = { ...fireCentreExpanded }
      newValue[fireCenterName] = isExpanded
      setFireCentreExpanded(newValue)
    }

  return (
    <div data-testid="provincial-summary">
      <InfoAccordion
        accordionDetailBackgroundColour={noProvincialSummary ? undefined : INFO_PANEL_CONTENT_BACKGORUND}
        defaultExpanded={true}
        title={'Provincial Summary'}
      >
        {noProvincialSummary ? (
          <Typography
            data-testid="provincial-summary-no-data"
            sx={{ paddingLeft: theme.spacing(4), paddingTop: theme.spacing(1) }}
          >
            {NO_DATA_MESSAGE}
          </Typography>
        ) : (
            Object.keys(provincialSummary)
              .sort((a, b) => a.localeCompare(b))
              .map(key => {
                return (
                  <FireCentreInfo
                    key={key}
                    advisoryThreshold={advisoryThreshold}
                  expanded={fireCentreExpanded[key]}
                  fireCentreName={key}
                  fireZoneUnitInfos={provincialSummary[key]}
                  onChangeExpaneded={handleFireCentreAccordionChanged}
                />
              )
            })
        )}
      </InfoAccordion>
    </div>
  )
}

export default ProvincialSummary
