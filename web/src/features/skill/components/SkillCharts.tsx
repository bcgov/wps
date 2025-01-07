import React from 'react'
import Plot from 'react-plotly.js'
import * as Plotly from 'plotly.js'
import { MORECAST_MODEL_COLORS } from 'app/theme'
import { Box, Button, Grid, Typography } from '@mui/material'

const SkillCharts = () => {
  const hrdps: Plotly.Data = {
    x: [0.2, -0.9, 0.6, -0.1, 2.5, 0.8, -0.3, 0.7, 0.2, 1.0],
    type: 'box',
    name: 'HRDPS',
    marker: { color: MORECAST_MODEL_COLORS.hrdps.border }
  }

  const rdps: Plotly.Data = {
    x: [0.3, -1.3, 0.9, -0.2, 2.5, 1.6, -0.5, 1.0, 0.3, 1.5],
    type: 'box',
    name: 'RDPS',
    marker: { color: MORECAST_MODEL_COLORS.rdps.border }
  }

  const gdps: Plotly.Data = {
    x: [0.4, -1.5, 2.0, -0.5, 3.3, 1.6, -0.3, 0.9, 0.6, 1.7],
    type: 'box',
    name: 'GDPS',
    marker: { color: MORECAST_MODEL_COLORS.gdps.border }
  }

  const nam: Plotly.Data = {
    x: [-0.4, 1.3, -0.6, 0.1, -2.5, -0.8, 0.3, -0.7, -0.2, -1.6],
    type: 'box',
    name: 'NAM',
    marker: { color: MORECAST_MODEL_COLORS.nam.border }
  }

  const gfs: Plotly.Data = {
    x: [1.3, 1.9, 3.3, 4.1, 2.5, 0.8, -1.0, 1.6, 0.9, 2.3],
    type: 'box',
    name: 'GFS',
    marker: { color: MORECAST_MODEL_COLORS.gfs.border }
  }

  // const data = [hrdps, rdps, gdps, nam, gfs]
  const data: Plotly.Data[] = [gfs, nam, gdps, rdps, hrdps]

  const layout = {
    height: 300,
    title: {
      text: 'Temperature Difference (Predicted - Observed) °C'
    }
  }
  return (
    <Box sx={{ display: 'flex', flexDirection: 'row' }}>
      <Box sx={{ padding: '32px', width: '300px' }}>
        <Typography sx={{ fontWeight: 'bold', paddingBottom: '32px' }}>Mean Squared Error</Typography>
        <Grid container sx={{ flexDirection: 'row' }} xs={12}>
          <Grid item xs={3}>
            <Typography sx={{ fontWeight: 'bold' }}>Model</Typography>
            <Typography sx={{ height: '32px' }}>HRDPS: </Typography>
            <Typography sx={{ height: '32px' }}>RDPS: </Typography>
            <Typography sx={{ height: '32px' }}>GDPS: </Typography>
            <Typography sx={{ height: '32px' }}>NAM: </Typography>
            <Typography sx={{ height: '32px' }}>GFS: </Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography sx={{ fontWeight: 'bold' }}>MSE</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>3.6</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>4.9</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>5.7</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>3.9</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>7.4</Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography sx={{ fontWeight: 'bold' }}>Rank</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>1</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>3</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>4</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>2</Typography>
            <Typography sx={{ paddingLeft: '16px', height: '32px' }}>5</Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography sx={{ fontWeight: 'bold' }}>Action</Typography>
            <Button sx={{ padding: '4px' }} size="small" variant="contained">
              Apply
            </Button>
            <Button size="small" variant="contained">
              Apply
            </Button>
            <Button size="small" variant="contained">
              Apply
            </Button>
            <Button size="small" variant="contained">
              Apply
            </Button>
            <Button size="small" variant="contained">
              Apply
            </Button>
          </Grid>
        </Grid>
      </Box>
      <Box>
        <Plot data={data} layout={layout} />
      </Box>
    </Box>
  )
}

export default SkillCharts
