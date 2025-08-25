import { FireCenter, FireShape } from "@/api/fbaAPI";
import { AppHeader } from "@/components/AppHeader";
import BottomNavigationBar from "@/components/BottomNavigationBar";
import ASAGoMap from "@/components/map/ASAGoMap";
import Profile from "@/components/profile/Profile";
import Advisory from "@/components/report/Advisory";
import TabPanel from "@/components/TabPanel";
import { useAppIsActive } from "@/hooks/useAppIsActive";
import { useRunParameterForDate } from "@/hooks/useRunParameterForDate";
import { fetchAndCacheData } from "@/slices/dataSlice";
import { fetchFireCenters } from "@/slices/fireCentersSlice";
import {
  startWatchingLocation,
  stopWatchingLocation,
} from "@/slices/geolocationSlice";
import { updateNetworkStatus } from "@/slices/networkStatusSlice";
import { fetchSFMSRunParameters } from "@/slices/runParametersSlice";
import { AppDispatch, selectFireCenters, selectNetworkStatus } from "@/store";
import { theme } from "@/theme";
import { NavPanel, PST_UTC_OFFSET } from "@/utils/constants";
import { ConnectionStatus, Network } from "@capacitor/network";
import { Box } from "@mui/material";
import { LicenseInfo } from "@mui/x-license-pro";
import { isNil, isNull } from "lodash";
import { DateTime } from "luxon";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

const ADVISORY_THRESHOLD = 20;

const App = () => {
  LicenseInfo.setLicenseKey(import.meta.env.VITE_MUI_LICENSE_KEY);
  const isActive = useAppIsActive();
  const dispatch: AppDispatch = useDispatch();

  // local state
  const [tab, setTab] = useState<NavPanel>(NavPanel.MAP);
  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(
    undefined
  );
  const [selectedFireShape, setSelectedFireShape] = useState<
    FireShape | undefined
  >(undefined);
  const [dateOfInterest, setDateOfInterest] = useState<DateTime>(
    DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
  );

  // selected redux state
  const { fireCenters } = useSelector(selectFireCenters);
  const { networkStatus } = useSelector(selectNetworkStatus);

  // hooks
  const runParameter = useRunParameterForDate(dateOfInterest);

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
    if (networkStatus.connected) {
      dispatch(fetchSFMSRunParameters());
    }
  }, [networkStatus.connected, dispatch]);

  useEffect(() => {
    dispatch(fetchFireCenters());
    const doiISODate = dateOfInterest.toISODate();
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunParameters());
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate();
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunParameters());
    }
  }, [dateOfInterest, networkStatus.connected]); // eslint-disable-line react-hooks/exhaustive-deps

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
    if (!isNil(runParameter)) {
      dispatch(fetchAndCacheData());
    }
  }, [runParameter, dispatch]);

  // start/stop watching location based on tab and app state
  useEffect(() => {
    if (isActive && tab === NavPanel.MAP) {
      dispatch(startWatchingLocation());
    } else {
      dispatch(stopWatchingLocation());
    }
  }, [isActive, tab, dispatch]);

  return (
    <Box
      id="asa-go-app"
      sx={{
        height: "100vh",
        padding: 0,
        margin: 0,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        paddingBottom: "env(safe-area-inset-bottom)",
        backgroundColor: theme.palette.primary.main,
      }}
    >
      <AppHeader />
      <Box
        sx={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <TabPanel value={tab} panel={NavPanel.MAP}>
          <ASAGoMap
            selectedFireShape={selectedFireShape}
            setSelectedFireShape={setSelectedFireShape}
            setSelectedFireCenter={setFireCenter}
            advisoryThreshold={ADVISORY_THRESHOLD}
            date={dateOfInterest}
            setDate={setDateOfInterest}
            setTab={setTab}
            testId="asa-go-map"
          />
        </TabPanel>
        <TabPanel value={tab} panel={NavPanel.PROFILE}>
          <Profile
            advisoryThreshold={ADVISORY_THRESHOLD}
            date={dateOfInterest}
            setDate={setDateOfInterest}
            selectedFireCenter={fireCenter}
            setSelectedFireCenter={setFireCenter}
            selectedFireZoneUnit={selectedFireShape}
            setSelectedFireZoneUnit={setSelectedFireShape}
          />
        </TabPanel>
        <TabPanel value={tab} panel={NavPanel.ADVISORY}>
          <Advisory
            advisoryThreshold={ADVISORY_THRESHOLD}
            date={dateOfInterest}
            setDate={setDateOfInterest}
            selectedFireCenter={fireCenter}
            setSelectedFireCenter={setFireCenter}
            selectedFireZoneUnit={selectedFireShape}
            setSelectedFireZoneUnit={setSelectedFireShape}
          />
        </TabPanel>
      </Box>
      <BottomNavigationBar tab={tab} setTab={setTab} />
    </Box>
  );
};

export default App;
