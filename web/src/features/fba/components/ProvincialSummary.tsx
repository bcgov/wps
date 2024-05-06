import React from 'react'
import { useSelector } from 'react-redux'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import FireCentreInfo from 'features/fba/components/FireCentreInfo'
import InfoAccordion from 'features/fba/components/InfoAccordion'
import { isNull, isUndefined } from 'lodash'
import { Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'

interface ProvincialSummaryProps {
  advisoryThreshold: number
}

// Displays advisory status of all fire zone units in all fire centres across BC.
const ProvincialSummary = ({ advisoryThreshold }: ProvincialSummaryProps) => {
  const provincialSummary = useSelector(selectProvincialSummary)
  const theme = useTheme()

  return (
    <InfoAccordion defaultExpanded={false} title={'Provincial Summary'}>
      {isNull(provincialSummary) || isUndefined(provincialSummary) || Object.keys(provincialSummary).length === 0 ? (
        <Typography sx={{ paddingTop: theme.spacing(1) }}>No data avaiable for the selected parameters</Typography>
      ) : (
        Object.keys(provincialSummary).map((key, index) => {
          return (
            <FireCentreInfo
              key={index}
              advisoryThreshold={advisoryThreshold}
              fireCentreName={key}
              fireZoneUnitInfos={provincialSummary[key]}
            />
          )
        })
      )}
    </InfoAccordion>
  )
}

export default ProvincialSummary
