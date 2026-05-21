import React from 'react'
import { Box, Tabs, Tab } from '@mui/material'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { ErrorBoundary } from '@wps/ui/ErrorBoundary'
import { AdapterLuxon } from '@mui/x-date-pickers-pro/AdapterLuxon'
import { LocalizationProvider } from '@mui/x-date-pickers-pro/LocalizationProvider'
import { SMURFI_DASHBOARD_ROUTE, SMURFI_MAP_ROUTE, SMURFI_MANAGEMENT_ROUTE } from '@wps/utils/constants'
import SpotManagement from '@/features/smurfi/components/management/SpotManagement'
import SMURFIMap from '@/features/smurfi/components/map/SMURFIMap'
import SpotRequests from '@/features/smurfi/components/requests/SpotRequests'
import SpotRequest from '@/features/smurfi/components/requests/SpotRequest'
import SpotForecasts from '@/features/smurfi/components/forecasts/SpotForecasts'
import SpotForecast from '@/features/smurfi/components/forecasts/SpotForecast'

const TAB_ROUTES = [SMURFI_DASHBOARD_ROUTE, SMURFI_MAP_ROUTE, SMURFI_MANAGEMENT_ROUTE]

const RouteContent = ({ children }: { children: React.ReactNode }) => (
  <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, p: 3 }}>{children}</Box>
)

const SMURFIPage = () => {
  const location = useLocation()
  const navigate = useNavigate()

  const activeTab = TAB_ROUTES.findIndex(route => location.pathname.startsWith(route))
  const currentTab = activeTab === -1 ? 0 : activeTab

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    navigate(TAB_ROUTES[newValue])
  }

  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <GeneralHeader isBeta={true} spacing={1} title="SMURFI" />
        <Tabs value={currentTab} onChange={handleChange}>
          <Tab label="Dashboard" />
          <Tab label="Map" />
          <Tab label="Spot Management" />
        </Tabs>
        <Box sx={{ flex: 1, minHeight: 0, display: 'flex' }}>
          <Routes>
            <Route
              path="requests/*"
              element={
                <RouteContent>
                  <Routes>
                    <Route index element={<SpotRequests />} />
                    <Route path=":id" element={<SpotRequest />} />
                    <Route path=":id/forecasts" element={<SpotForecasts />} />
                    <Route path=":id/forecasts/:forecastId" element={<SpotForecast />} />
                  </Routes>
                </RouteContent>
              }
            />
            <Route
              path="map"
              element={
                <RouteContent>
                  <ErrorBoundary>
                    <SMURFIMap />
                  </ErrorBoundary>
                </RouteContent>
              }
            />
            <Route
              path="management"
              element={
                <RouteContent>
                  <SpotManagement />
                </RouteContent>
              }
            />
            <Route path="*" element={<Navigate to={SMURFI_DASHBOARD_ROUTE} replace />} />
          </Routes>
        </Box>
      </Box>
    </LocalizationProvider>
  )
}

export default SMURFIPage
