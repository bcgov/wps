import { AppDispatch } from '@/app/store'
import { fetchFireCentres } from '@/commonSlices/fireCentresSlice'
import DistributionGroupsAdmin from '@/features/smurfi/components/admin/DistributionGroupsAdmin'
import SpotForecastFormPage from '@/features/smurfi/components/forecastForm/SpotForecastFormPage'
import SpotForecast from '@/features/smurfi/components/forecasts/SpotForecast'
import SpotForecasts from '@/features/smurfi/components/forecasts/SpotForecasts'
import SMURFIMap from '@/features/smurfi/components/map/SMURFIMap'
import SpotRequestFormPage from '@/features/smurfi/components/requestForm/SpotRequestFormPage'
import SpotRequest from '@/features/smurfi/components/requests/SpotRequest'
import SpotRequests from '@/features/smurfi/components/requests/SpotRequests'
import PrintableSpotForecast from '@/features/smurfi/pages/PrintableSpotForecast'
import EditSpotForecastPage from '@/features/smurfi/pages/EditSpotForecastPage'
import { fetchSpotRequests } from '@/features/smurfi/slices/smurfiSlice'
import { fetchSubscriptions } from '@/features/smurfi/slices/subscriptionsSlice'
import { fetchWxStations } from '@/features/stations/slices/stationsSlice'
import { Box, Tab, Tabs } from '@mui/material'
import { AdapterLuxon } from '@mui/x-date-pickers-pro/AdapterLuxon'
import { LocalizationProvider } from '@mui/x-date-pickers-pro/LocalizationProvider'
import { getStations, StationSource } from '@wps/api/stationAPI'
import { ErrorBoundary } from '@wps/ui/ErrorBoundary'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { SMURFI_DASHBOARD_ROUTE, SMURFI_ADMIN_ROUTE, SMURFI_MAP_ROUTE } from '@wps/utils/constants'
import React, { useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

const TAB_ROUTES = [SMURFI_DASHBOARD_ROUTE, SMURFI_MAP_ROUTE, SMURFI_ADMIN_ROUTE]

const RouteContent = ({ children, fullBleed = false }: { children: React.ReactNode; fullBleed?: boolean }) => (
  <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, p: fullBleed ? 0 : 3 }}>{children}</Box>
)

const SMURFIPage = () => {
  const dispatch: AppDispatch = useDispatch()
  useEffect(() => {
    dispatch(fetchSpotRequests())
    dispatch(fetchSubscriptions())
    dispatch(fetchFireCentres())
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, [])
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
        <Box sx={{ display: location.pathname.endsWith('/print') ? 'none' : 'block' }}>
          <GeneralHeader isBeta={true} spacing={1} title="SMURFI" />
          <Tabs value={currentTab} onChange={handleChange}>
            <Tab label="Dashboard" onClick={() => navigate(SMURFI_DASHBOARD_ROUTE)} />
            <Tab label="Map" onClick={() => navigate(SMURFI_MAP_ROUTE)} />
            <Tab label="Admin" onClick={() => navigate(SMURFI_ADMIN_ROUTE)} />
          </Tabs>
        </Box>
        <Box sx={{ flex: 1, minHeight: 0, display: 'flex' }}>
          <Routes>
            <Route
              path="requests/*"
              element={
                <RouteContent>
                  <Routes>
                    <Route index element={<SpotRequests />} />
                    <Route path="new" element={<SpotRequestFormPage />} />
                    <Route path=":id" element={<SpotRequest />} />
                    <Route path=":id/forecasts" element={<SpotForecasts />} />
                    <Route path=":id/forecasts/new" element={<SpotForecastFormPage />} />
                    <Route path=":id/forecasts/:forecastId" element={<SpotForecast />} />
                    <Route path=":id/forecasts/:forecastId/print" element={<PrintableSpotForecast />} />
                    <Route path=":id/forecasts/:forecastId/edit" element={<EditSpotForecastPage />} />
                  </Routes>
                </RouteContent>
              }
            />
            <Route
              path="map"
              element={
                <RouteContent fullBleed>
                  <ErrorBoundary>
                    <SMURFIMap />
                  </ErrorBoundary>
                </RouteContent>
              }
            />
            <Route
              path="admin"
              element={
                <RouteContent>
                  <DistributionGroupsAdmin />
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
