import React, { Suspense, lazy } from 'react'
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'

import AuthWrapper from '@/features/auth/components/AuthWrapper'
import FireWatchPage from '@/features/fireWatch/pages/FireWatchPage'
import { SFMSInsightsPage } from '@/features/sfmsInsights/pages/SFMSInsightsPage'
import WeatherToolkitPage from '@/features/weatherToolkit/pages/WeatherToolkitPage'
import {
  C_HAINES_ROUTE,
  FIRE_BEHAVIOR_CALC_ROUTE,
  FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  FIRE_WATCH_ROUTE,
  HFI_CALC_ROUTE,
  LANDING_PAGE_ROUTE,
  MORECAST_ROUTE,
  MORE_CAST_2_ROUTE,
  PERCENTILE_CALC_ROUTE,
  SFMS_INSIGHTS_ROUTE,
  SMURFI_ROUTE,
  WEATHER_TOOLKIT_ROUTE
} from '@wps/utils/constants'
import { HIDE_DISCLAIMER } from '@wps/utils/env'
import { NoMatchPage } from 'features/NoMatchPage'
import LoadingBackdrop from 'features/hfiCalculator/components/LoadingBackdrop'
const PercentileCalculatorPageWithDisclaimer = lazy(
  () => import('features/percentileCalculator/pages/PercentileCalculatorPageWithDisclaimer')
)
const HfiCalculatorPage = lazy(() => import('features/hfiCalculator/pages/HfiCalculatorPage'))
const CHainesPage = lazy(() => import('features/cHaines/pages/CHainesPage'))
const FireBehaviourCalculator = lazy(() => import('features/fbaCalculator/pages/FireBehaviourCalculatorPage'))
const FireBehaviourAdvisoryPage = lazy(() => import('features/fba/pages/FireBehaviourAdvisoryPage'))
const LandingPage = lazy(() => import('features/landingPage/pages/LandingPage'))
const MoreCast2Page = lazy(() => import('features/moreCast2/pages/MoreCast2Page'))
const SMURFIPage = lazy(() => import('features/smurfi/pages/SMURFIPage'))

const shouldShowDisclaimer = HIDE_DISCLAIMER === 'false' || HIDE_DISCLAIMER === undefined

const WPSRoutes: React.FunctionComponent = () => {
  return (
    <Router>
      <Suspense fallback={<LoadingBackdrop isLoadingWithoutError={true} />}>
        <Routes>
          <Route
            path={LANDING_PAGE_ROUTE}
            element={
              <React.StrictMode>
                <LandingPage />
              </React.StrictMode>
            }
          />
          <Route
            path={PERCENTILE_CALC_ROUTE}
            element={
              <React.StrictMode>
                <PercentileCalculatorPageWithDisclaimer showDisclaimer={shouldShowDisclaimer} />
              </React.StrictMode>
            }
          />
          <Route
            path={HFI_CALC_ROUTE}
            element={
              <AuthWrapper>
                <HfiCalculatorPage />
              </AuthWrapper>
            }
          />
          <Route
            path={C_HAINES_ROUTE}
            element={
              <React.StrictMode>
                <CHainesPage />
              </React.StrictMode>
            }
          />
          <Route
            path={FIRE_BEHAVIOR_CALC_ROUTE}
            element={
              <AuthWrapper>
                <FireBehaviourCalculator />
              </AuthWrapper>
            }
          />
          <Route
            path={FIRE_BEHAVIOUR_ADVISORY_ROUTE}
            element={
              <AuthWrapper>
                <FireBehaviourAdvisoryPage />
              </AuthWrapper>
            }
          />
          <Route path={MORE_CAST_2_ROUTE} element={<Navigate to={MORECAST_ROUTE} />} />
          <Route
            path={MORECAST_ROUTE}
            element={
              <AuthWrapper>
                <MoreCast2Page />
              </AuthWrapper>
            }
          />
          <Route
            path={SFMS_INSIGHTS_ROUTE}
            element={
              <AuthWrapper>
                <SFMSInsightsPage />
              </AuthWrapper>
            }
          />
          <Route
            path={FIRE_WATCH_ROUTE}
            element={
              <AuthWrapper>
                <FireWatchPage />
              </AuthWrapper>
            }
          />
          <Route path={WEATHER_TOOLKIT_ROUTE} element={<WeatherToolkitPage />} />
          <Route
            path={SMURFI_ROUTE}
            element={
              <AuthWrapper>
                <SMURFIPage />
              </AuthWrapper>
            }
          />
          <Route path="*" element={<NoMatchPage />} />
        </Routes>
      </Suspense>
    </Router>
  )
}

export default React.memo(WPSRoutes)
