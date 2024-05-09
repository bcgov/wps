import React from 'react'
import { useSelector } from 'react-redux'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import FireCentreInfo from 'features/fba/components/infoPanel/FireCentreInfo'
import InfoAccordion from 'features/fba/components/infoPanel/InfoAccordion'
import { isNull, isUndefined } from 'lodash'
import { Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'

interface ProvincialSummaryProps {
  advisoryThreshold: number
}

export const NO_DATA_MESSAGE = 'No data available for the selected parameters.'

// Displays advisory status of all fire zone units in all fire centres across BC.
const ProvincialSummary = ({ advisoryThreshold }: ProvincialSummaryProps) => {
  const provincialSummary = useSelector(selectProvincialSummary)
  const theme = useTheme()

  return (
    <div data-testid="provincial-summary">
      <InfoAccordion defaultExpanded={true} title={'Provincial Summary'}>
        {isNull(provincialSummary) || isUndefined(provincialSummary) || Object.keys(provincialSummary).length === 0 ? (
          <Typography data-testid="provincial-summary-no-data" sx={{ paddingTop: theme.spacing(1) }}>
            {NO_DATA_MESSAGE}
          </Typography>
        ) : (
          Object.keys(provincialSummary).map(key => {
            return (
              <FireCentreInfo
                key={key}
                advisoryThreshold={advisoryThreshold}
                fireCentreName={key}
                fireZoneUnitInfos={provincialSummary[key]}
              />
            )
          })
        )}
      </InfoAccordion>
    </div>
  )
}

export default ProvincialSummary
