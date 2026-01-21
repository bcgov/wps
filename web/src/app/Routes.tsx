import React, { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom'

import { HIDE_DISCLAIMER } from 'utils/env'
import AuthWrapper from 'features/auth/components/AuthWrapper'
const PercentileCalculatorPageWithDisclaimer = lazy(
  () => import('features/percentileCalculator/pages/PercentileCalculatorPageWithDisclaimer')
)
const HfiCalculatorPage = lazy(() => import('features/hfiCalculator/pages/HfiCalculatorPage'))
const CHainesPage = lazy(() => import('features/cHaines/pages/CHainesPage'))
import {
  PERCENTILE_CALC_ROUTE,
  HFI_CALC_ROUTE,
  MORECAST_ROUTE,
  C_HAINES_ROUTE,
  FIRE_BEHAVIOR_CALC_ROUTE,
  FIRE_BEHAVIOUR_ADVISORY_ROUTE,
  LANDING_PAGE_ROUTE,
  MORE_CAST_2_ROUTE,
  SFMS_INSIGHTS_ROUTE,
  FIRE_WATCH_ROUTE,
  CLIMATOLOGY_ROUTE
} from 'utils/constants'
import { NoMatchPage } from 'features/NoMatchPage'
const FireBehaviourCalculator = lazy(() => import('features/fbaCalculator/pages/FireBehaviourCalculatorPage'))
const FireBehaviourAdvisoryPage = lazy(() => import('features/fba/pages/FireBehaviourAdvisoryPage'))
const LandingPage = lazy(() => import('features/landingPage/pages/LandingPage'))
const MoreCast2Page = lazy(() => import('features/moreCast2/pages/MoreCast2Page'))
import LoadingBackdrop from 'features/hfiCalculator/components/LoadingBackdrop'
import { SFMSInsightsPage } from '@/features/sfmsInsights/pages/SFMSInsightsPage'
import FireWatchPage from '@/features/fireWatch/pages/FireWatchPage'
const ClimatologyPage = lazy(() => import('features/climatology/pages/ClimatologyPage'))

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
          <Route
            path={CLIMATOLOGY_ROUTE}
            element={
              <AuthWrapper>
                <ClimatologyPage />
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
