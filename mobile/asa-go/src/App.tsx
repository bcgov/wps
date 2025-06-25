import { useEffect, useState } from "react";
import { Box } from "@mui/material";
import {
  Routes,
  Route,
  useNavigate,
  useLocation,
  BrowserRouter,
} from "react-router-dom";

import FBAMap from "@/components/map/FBAMap";
import { FireCenter, FireShape, RunType } from "@/api/fbaAPI";
import { AppHeader } from "@/components/AppHeader";
import { useDispatch, useSelector } from "react-redux";
import { DateTime } from "luxon";
import { NavPanel, PST_UTC_OFFSET } from "@/utils/constants";
import {
  selectFireCenters,
  selectRunDates,
  selectFireShapeAreas,
  AppDispatch,
} from "@/store";
import { isNull, isUndefined } from "lodash";
import { fetchSFMSRunDates } from "@/slices/runDatesSlice";
import { fetchFireCenters } from "@/slices/fireCentersSlice";
import { fetchFireCentreTPIStats } from "@/slices/fireCentreTPIStatsSlice";
import { fetchFireCentreHFIFuelStats } from "@/slices/fireCentreHFIFuelStatsSlice";
import { fetchFireShapeAreas } from "@/slices/fireZoneAreasSlice";
import { fetchProvincialSummary } from "@/slices/provincialSummarySlice";
import { updateNetworkStatus } from "@/slices/networkStatusSlice";
import { ConnectionStatus, Network } from "@capacitor/network";
import Profile from "@/components/Profile";
import Advisory from "@/components/Advisory";
import BottomNavigationBar from "@/components/BottomNavigationBar";
import React from "react";

const AppContent = () => {
  const dispatch: AppDispatch = useDispatch();
  const { fireCenters } = useSelector(selectFireCenters);
  const navigate = useNavigate();
  const location = useLocation();

  let activeTab: NavPanel;
  if (location.pathname === "/profile") activeTab = NavPanel.PROFILE;
  else if (location.pathname === "/advisory") activeTab = NavPanel.ADVISORY;
  else activeTab = NavPanel.MAP;

  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(
    undefined
  );

  const [selectedFireShape] = useState<FireShape | undefined>(undefined);
  const [zoomSource] = useState<"fireCenter" | "fireShape" | undefined>(
    "fireCenter"
  );
  const [dateOfInterest] = useState(
    DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).hour < 13
      ? DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
      : DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).plus({ days: 1 })
  );
  const [runType] = useState(RunType.FORECAST);
  const { mostRecentRunDate } = useSelector(selectRunDates);
  const { fireShapeAreas } = useSelector(selectFireShapeAreas);

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate();
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate));
    }
  }, [runType]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Network status is disconnected by default in the networkStatusSlice. Update the status
    // when the app first starts and then attach a listener to keep network status in the redux
    // store current.
    async function getInitialNetworkStatus() {
      const status = await Network.getStatus();
      dispatch(updateNetworkStatus(status));
    }
    getInitialNetworkStatus();
    Network.addListener("networkStatusChange", (status: ConnectionStatus) => {
      console.log(
        `Network status changed: ${status.connected}, ${status.connectionType}`
      );
      dispatch(updateNetworkStatus(status));
    });
    return () => {
      Network.removeAllListeners();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    dispatch(fetchFireCenters());
    const doiISODate = dateOfInterest.toISODate();
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate();
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate));
    }
  }, [dateOfInterest]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedFireShape?.mof_fire_centre_name) {
      const matchingFireCenter = fireCenters.find(
        (center) => center.name === selectedFireShape.mof_fire_centre_name
      );

      if (matchingFireCenter) {
        setFireCenter(matchingFireCenter);
      }
    }
  }, [selectedFireShape, fireCenters]);

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate();
    if (
      !isNull(mostRecentRunDate) &&
      !isNull(doiISODate) &&
      !isUndefined(mostRecentRunDate) &&
      !isUndefined(fireCenter) &&
      !isNull(fireCenter)
    ) {
      dispatch(
        fetchFireCentreTPIStats(
          fireCenter.name,
          runType,
          doiISODate,
          mostRecentRunDate.toString()
        )
      );
      dispatch(
        fetchFireCentreHFIFuelStats(
          fireCenter.name,
          runType,
          doiISODate,
          mostRecentRunDate.toString()
        )
      );
    }
  }, [fireCenter, mostRecentRunDate]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate();
    if (!isNull(doiISODate)) {
      dispatch(fetchFireShapeAreas(runType, mostRecentRunDate, doiISODate));
      dispatch(fetchProvincialSummary(runType, mostRecentRunDate, doiISODate));
    }
  }, [mostRecentRunDate]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Box
      sx={{
        height: "100vh",
        padding: 0,
        margin: 0,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <AppHeader />
      <Routes>
        <Route
          path="/"
          element={
            <FBAMap
              selectedFireCenter={fireCenter}
              selectedFireShape={selectedFireShape}
              fireShapeAreas={fireShapeAreas}
              zoomSource={zoomSource}
              advisoryThreshold={0}
            />
          }
        />

        <Route path="/profile" element={<Profile />} />
        <Route path="/advisory" element={<Advisory />} />
      </Routes>

      <BottomNavigationBar
        tab={activeTab}
        setTab={(newTab) => {
          if (newTab === NavPanel.MAP) navigate("/");
          if (newTab === NavPanel.PROFILE) navigate("/profile");
          if (newTab === NavPanel.ADVISORY) navigate("/advisory");
        }}
      />
    </Box>
  );
};

const App = () => (
  <BrowserRouter>
    <AppContent />
  </BrowserRouter>
);

export default React.memo(App);
