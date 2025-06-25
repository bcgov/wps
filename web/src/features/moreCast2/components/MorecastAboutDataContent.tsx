import React from 'react'
import {
  List,
  ListItem,
  ListItemText,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  styled
} from '@mui/material'

const StyledListItemText = styled(ListItemText)(({ theme }) => ({
  '& .MuiTypography-root': {
    fontSize: 'inherit'
  }
}))

const MorecastAboutDataContent = () => (
  <Box data-testid="morecast-about-data-content" sx={{ fontSize: '0.9rem' }}>
    <List disablePadding>
      <ListItem disableGutters>
        <Box>
          <Typography fontSize="inherit" fontWeight="bold">
            Temp, RH, Wind Speed/Direction
          </Typography>
          <StyledListItemText
            primary="Some numerical weather prediction (NWP) models predict for 20:00 UTC (13:00 PDT), while others do not. 
            For models that do, these columns contain raw prediction values from the NWP models."
          />
        </Box>
      </ListItem>
      <ListItem disableGutters>
        <StyledListItemText
          primary="For models with 3 or 6-hour prediction intervals, 20:00 UTC values are linearly
        interpolated from surrounding predictions (e.g., 18:00 and 21:00 or 24:00 UTC)."
        />
      </ListItem>
      <ListItem disableGutters>
        <Box>
          <Typography fontSize="inherit" fontWeight="bold">
            Precipitation
          </Typography>
          <StyledListItemText
            primary="Precipitation is the 24-hour total from a single model run. For forecast hours earlier
          than hour 24, where the model does not provide a full 24-hour accumulation, observed
          station data is used to fill in the missing values."
          />
        </Box>
      </ListItem>
      <ListItem disableGutters>
        <Box>
          <Typography fontSize="inherit" fontWeight="bold">
            Bias-adjusted Values
          </Typography>
          <StyledListItemText
            primary="Bias-adjusted values are calculated using a linear regression trained 
        on the past 19 days of model predictions and corresponding observations. This correction is applied on 
        a per-station basis to improve model accuracy."
          />
        </Box>
      </ListItem>
    </List>

    <Box mt={3}>
      <Typography fontWeight="bold" fontSize={'inherit'}>
        Model Run Hours
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 1 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>
                <strong>Model</strong>
              </TableCell>
              <TableCell>
                <strong>Run Hours (UTC)</strong>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {[
              ['HRDPS', '0, 6, 12, 18'],
              ['GDPS', '0, 12'],
              ['RDPS', '0, 6, 12, 18'],
              ['GFS', '0, 6, 12, 18'],
              ['NAM', '0, 6, 12, 18']
            ].map(([model, hours]) => (
              <TableRow key={model}>
                <TableCell>{model}</TableCell>
                <TableCell>{hours}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  </Box>
)

export default MorecastAboutDataContent
