import {
  Box,
  List,
  ListItem,
  ListItemText,
  Paper,
  styled,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from '@mui/material'

const StyledListItemText = styled(ListItemText)(() => ({
  '& .MuiTypography-root': {
    fontSize: 'inherit'
  }
}))

const MorecastAboutDataContent = () => (
  <Box data-testid="morecast-about-data-content" sx={{ fontSize: '0.9rem' }}>
    <List disablePadding>
      <ListItem disableGutters>
        <Box>
          <Typography
            sx={{
              fontSize: 'inherit',
              fontWeight: 'bold'
            }}
          >
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
          <Typography
            sx={{
              fontSize: 'inherit',
              fontWeight: 'bold'
            }}
          >
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
          <Typography
            sx={{
              fontSize: 'inherit',
              fontWeight: 'bold'
            }}
          >
            Bias-adjusted Values
          </Typography>
          <StyledListItemText
            primary="Bias-adjusted values are calculated using a linear regression trained 
        on the past 19 days of model predictions and corresponding observations. This correction is applied on 
        a per-station basis to improve model accuracy."
          />
        </Box>
      </ListItem>
      <ListItem disableGutters>
        <Box>
          <Typography
            sx={{
              fontSize: 'inherit',
              fontWeight: 'bold'
            }}
          >
            Grass Curing
          </Typography>
          <StyledListItemText
            primary="Grass curing data for each station is extracted from raster data provided by the 
             Canadian Wildland Fire Information System (CWFIS)."
          />
        </Box>
      </ListItem>
    </List>

    <Box
      sx={{
        mt: 3
      }}
    >
      <Typography
        sx={{
          fontWeight: 'bold',
          fontSize: 'inherit'
        }}
      >
        Model resolution and run hours
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
              <TableCell>
                <strong>Grid spacing</strong>
              </TableCell>
              <TableCell>
                <strong>Approx. spacing in BC</strong>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {[
              ['HRDPS', '0, 6, 12, 18', '0.0225° rotated', '≈2.5 km'],
              ['GDPS', '0, 12', '0.15°', '≈17 × 10 km'],
              ['RDPS', '0, 6, 12, 18', '0.09° rotated', '≈10 km'],
              ['ECMWF', '0, 12', '0.1°', '≈11 × 6 km'],
              ['GFS', '0, 6, 12, 18', '0.25°', '≈28 × 16 km'],
              ['NAM', '0, 6, 12, 18', '12 km', '12 km']
            ].map(([model, hours, resolution, approximateSpacing]) => (
              <TableRow key={model}>
                <TableCell>{model}</TableCell>
                <TableCell sx={{ whiteSpace: 'nowrap' }}>{hours}</TableCell>
                <TableCell>{resolution}</TableCell>
                <TableCell sx={{ whiteSpace: 'nowrap' }}>{approximateSpacing}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        Paired distances show approximate spacing north to south × east to west at 55°N in BC. Spacing varies with
        latitude.
      </Typography>
    </Box>
  </Box>
)

export default MorecastAboutDataContent
