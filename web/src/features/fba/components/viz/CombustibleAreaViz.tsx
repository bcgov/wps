import React from 'react'
import { styled } from '@mui/material/styles'
import { FireZoneArea } from 'api/fbaAPI'
import { BarChart, CartesianGrid, XAxis, YAxis, Bar, Tooltip, ResponsiveContainer } from 'recharts'
import { Typography } from '@mui/material'
const PREFIX = 'CombustibleAreaViz'

const classes = {
  combustibleLandHeader: `${PREFIX}-combustibleLandHeader`
}

// TODO jss-to-styled codemod: The Fragment root was replaced by div. Change the tag if needed.
const Root = styled('div')({
  [`& .${classes.combustibleLandHeader}`]: {
    fontSize: '1.3rem',
    textAlign: 'center',
    variant: 'h3'
  }
})

export interface AdvisoryMetadataProps {
  testId?: string
  fireZoneAreas: FireZoneArea[]
}

const CombustibleAreaViz = ({ fireZoneAreas }: AdvisoryMetadataProps) => {
  const labelledFireZones = fireZoneAreas.map(area => ({
    ...area,
    threshold_label: area.threshold == 1 ? 'Advisory' : 'Warning',
    advisory_hfi_percentage: area.threshold == 1 ? area.elevated_hfi_percentage : undefined,
    warning_hfi_percentage: area.threshold == 2 ? area.elevated_hfi_percentage : undefined
  }))
  return (
    <Root>
      <Typography className={classes.combustibleLandHeader}>Combustible Land Under Advisory or Warning</Typography>
      <ResponsiveContainer width={400} height={250}>
        <BarChart data={labelledFireZones}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="threshold_label" />
          <YAxis label={{ value: '% of combustible land', angle: -90, position: 'center' }} />
          <Tooltip />
          <Bar dataKey="elevated_hfi_percentage" fill="#1E90FF" />
        </BarChart>
      </ResponsiveContainer>
    </Root>
  )
}

export default React.memo(CombustibleAreaViz)
