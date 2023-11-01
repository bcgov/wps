import React from 'react'
import { styled } from '@mui/material/styles'
import { FireShapeArea } from 'api/fbaAPI'
import { BarChart, CartesianGrid, XAxis, YAxis, Bar, Tooltip, ResponsiveContainer } from 'recharts'
import { Typography } from '@mui/material'
const PREFIX = 'CombustibleAreaViz'

const StyledTypography = styled(Typography, {
  name: `${PREFIX}-Typography`
})({
  fontSize: '1.3rem',
  textAlign: 'center',
  variant: 'h3'
})

export interface AdvisoryMetadataProps {
  testId?: string
  fireZoneAreas: FireShapeArea[]
}

const CombustibleAreaViz = ({ fireZoneAreas }: AdvisoryMetadataProps) => {
  const labelledFireZones = fireZoneAreas.map(area => ({
    ...area,
    threshold_label: area.threshold == 1 ? 'Advisory' : 'Warning',
    advisory_hfi_percentage: area.threshold == 1 ? area.elevated_hfi_percentage : undefined,
    warning_hfi_percentage: area.threshold == 2 ? area.elevated_hfi_percentage : undefined
  }))
  return (
    <div>
      <StyledTypography>Combustible Land Under Advisory or Warning</StyledTypography>
      <ResponsiveContainer width={400} height={250}>
        <BarChart data={labelledFireZones}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="threshold_label" />
          <YAxis label={{ value: '% of combustible land', angle: -90, position: 'center' }} />
          <Tooltip />
          <Bar dataKey="elevated_hfi_percentage" fill="#1E90FF" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default React.memo(CombustibleAreaViz)
