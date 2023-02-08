import React from 'react'
import { FireZoneArea } from 'api/fbaAPI'
import { BarChart, CartesianGrid, XAxis, YAxis, Bar, Tooltip, ResponsiveContainer } from 'recharts'
import { Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'

export interface AdvisoryMetadataProps {
  testId?: string
  fireZoneAreas: FireZoneArea[]
}

const useStyles = makeStyles({
  combustibleLandHeader: {
    fontSize: '1.3rem',
    textAlign: 'center',
    variant: 'h3'
  }
})

const CombustibleAreaViz = ({ fireZoneAreas }: AdvisoryMetadataProps) => {
  const classes = useStyles()

  const labelledFireZones = fireZoneAreas.map(area => ({
    ...area,
    threshold_label: area.threshold == 1 ? 'Advisory' : 'Warning',
    advisory_hfi_percentage: area.threshold == 1 ? area.elevated_hfi_percentage : undefined,
    warning_hfi_percentage: area.threshold == 2 ? area.elevated_hfi_percentage : undefined
  }))
  return (
    <>
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
    </>
  )
}

export default React.memo(CombustibleAreaViz)
