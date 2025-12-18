import React, { useState } from 'react'
import { useSelector } from 'react-redux'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import FireCentreInfo from 'features/fba/components/infoPanel/FireCentreInfo'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { isNull, isUndefined } from 'lodash'
import { Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { INFO_PANEL_CONTENT_BACKGROUND } from 'app/theme'
import { FireCentres } from 'utils/constants'

export const NO_DATA_MESSAGE = 'Choose a date of interest above.'

// Displays advisory status of all fire zone units in all fire centres across BC.
const ProvincialSummary = () => {
  const [fireCentreExpanded, setFireCentreExpanded] = useState<Record<string, boolean>>({
    [FireCentres.CARIBOO_FC]: false,
    [FireCentres.COASTAL_FC]: false,
    [FireCentres.KAMLOOPS_FC]: false,
    [FireCentres.NORTHWEST_FC]: false,
    [FireCentres.PRINCE_GEORGE_FC]: false,
    [FireCentres.SOUTHEAST_FC]: false
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

  const renderNoDataMessage = () => {
    return (
      <Typography
        data-testid="provincial-summary-no-data"
        sx={{ paddingLeft: theme.spacing(4), paddingTop: theme.spacing(1) }}
      >
        {NO_DATA_MESSAGE}
      </Typography>
    )
  }

  const renderFireCentreInfos = () => {
    const sortedKeys = Object.keys(provincialSummary).sort((a, b) => a.localeCompare(b))
    return sortedKeys.map(key => {
      return (
        <FireCentreInfo
          key={key}
          expanded={fireCentreExpanded[key]}
          fireCentreName={key}
          fireZoneUnitInfos={provincialSummary[key]}
          onChangeExpanded={handleFireCentreAccordionChanged}
        />
      )
    })
  }

  return (
    <div data-testid="provincial-summary">
      <InfoAccordion
        accordionDetailBackgroundColour={noProvincialSummary ? undefined : INFO_PANEL_CONTENT_BACKGROUND}
        defaultExpanded={true}
        title={'Provincial Summary'}
      >
        {noProvincialSummary ? renderNoDataMessage() : renderFireCentreInfos()}
      </InfoAccordion>
    </div>
  )
}

export default ProvincialSummary
