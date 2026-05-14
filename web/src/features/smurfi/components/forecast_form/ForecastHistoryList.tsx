import React from 'react'
import { Box, Card, CardContent, Typography, List, ListItemButton, ListItemText, Chip, Divider } from '@mui/material'
import { DateTime } from 'luxon'
import { SpotForecastHistoryItem, SpotForecastStatusColorMap } from '@/features/smurfi/interfaces'

interface ForecastHistoryListProps {
  forecasts: SpotForecastHistoryItem[]
  selectedId: number | null
  onSelectForecast: (forecast: SpotForecastHistoryItem) => void
}

const ForecastHistoryList: React.FC<ForecastHistoryListProps> = ({ forecasts, selectedId, onSelectForecast }) => {
  if (forecasts.length === 0) {
    return null
  }

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Forecast History
        </Typography>
        <Divider sx={{ mb: 1 }} />
        <List dense disablePadding>
          {forecasts.map((forecast, index) => {
            const isSelected = selectedId === forecast.id
            const statusColors = SpotForecastStatusColorMap[forecast.status]
            const issuedDate = DateTime.fromMillis(forecast.issued_date)
            const isMostRecent = index === 0

            return (
              <ListItemButton
                key={forecast.id}
                selected={isSelected}
                onClick={() => onSelectForecast(forecast)}
                sx={{
                  borderRadius: 1,
                  mb: 0.5,
                  border: isSelected ? '2px solid #1976d2' : '1px solid #e0e0e0',
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(25, 118, 210, 0.08)'
                  }
                }}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" fontWeight="medium">
                        {issuedDate.toFormat('MMM dd, yyyy HH:mm')}
                      </Typography>
                      {isMostRecent && (
                        <Chip
                          label="Current"
                          size="small"
                          color="primary"
                          sx={{
                            fontSize: '0.7rem',
                            height: 20
                          }}
                        />
                      )}
                      <Chip
                        label={forecast.status}
                        size="small"
                        sx={{
                          backgroundColor: statusColors.bgColor,
                          color: statusColors.color,
                          border: `1px solid ${statusColors.borderColor}`,
                          fontSize: '0.7rem',
                          height: 20
                        }}
                      />
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary" component="span">
                      By {forecast.forecaster} • {forecast.synopsis.substring(0, 60)}
                      {forecast.synopsis.length > 60 ? '...' : ''}
                    </Typography>
                  }
                />
              </ListItemButton>
            )
          })}
        </List>
      </CardContent>
    </Card>
  )
}

export default ForecastHistoryList
