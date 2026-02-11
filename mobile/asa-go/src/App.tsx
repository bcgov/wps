import { FireCenter, FireShape } from "@/api/fbaAPI";
import { AppHeader } from "@/components/AppHeader";
import BottomNavigationBar from "@/components/BottomNavigationBar";
import SideNavigation from "@/components/SideNavigation";
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
import {
  AppDispatch,
  selectFireCenters,
  selectNetworkStatus,
  selectRunParameters,
} from "@/store";
import { theme } from "@/theme";
import { NavPanel } from "@/utils/constants";
import { today } from "@/utils/dataSliceUtils";
import { PMTilesCache } from "@/utils/pmtilesCache";
import { clearStaleHFIPMTiles } from "@/utils/storage";
import { Filesystem } from "@capacitor/filesystem";
import { ConnectionStatus, Network } from "@capacitor/network";
import { ScreenOrientation } from "@capacitor/screen-orientation";
import { StatusBar } from "@capacitor/status-bar";
import { Box, useMediaQuery } from "@mui/material";
import { LicenseInfo } from "@mui/x-license-pro";
import { isNil, isNull } from "lodash";
import { DateTime } from "luxon";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

const App = () => {
  LicenseInfo.setLicenseKey(import.meta.env.VITE_MUI_LICENSE_KEY);
  const isActive = useAppIsActive();
  const dispatch: AppDispatch = useDispatch();
  const [isPortrait, setIsPortrait] = useState<boolean>(true);
  const isSmallScreen = useMediaQuery(theme.breakpoints.down("md"));

  // local state
  const [tab, setTab] = useState<NavPanel>(NavPanel.MAP);
  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(
    undefined,
  );
  const [selectedFireShape, setSelectedFireShape] = useState<
    FireShape | undefined
  >(undefined);
  const [dateOfInterest, setDateOfInterest] = useState<DateTime>(today);

  // selected redux state
  const { fireCenters } = useSelector(selectFireCenters);
  const { networkStatus } = useSelector(selectNetworkStatus);
  const runParameters = useSelector(selectRunParameters);

  // hooks
  const runParameter = useRunParameterForDate(dateOfInterest);

  useEffect(() => {
    // Effect to manage status bar visibility
    const handleOrientationChange = async () => {
      const info = await ScreenOrientation.orientation();
      if (info.type.includes("landscape")) {
        // Device is in landscape mode
        await StatusBar.hide();
        setIsPortrait(false);
      } else {
        // Device is in portrait mode
        await StatusBar.show();
        setIsPortrait(true);
      }
    };

    // Add the listener
    ScreenOrientation.addListener(
      "screenOrientationChange",
      handleOrientationChange,
    );

    // Call it initially in case the app starts in landscape
    handleOrientationChange();

    return () => {
      ScreenOrientation.removeAllListeners();
    };
  }, []);

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
        `Network status changed: ${status.connected}, ${status.connectionType}`,
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
        (center) => center.name === selectedFireShape.mof_fire_centre_name,
      );

      if (matchingFireCenter) {
        setFireCenter(matchingFireCenter);
      }
    }
  }, [selectedFireShape, fireCenters]);

  useEffect(() => {
    if (!isNil(runParameters)) {
      const hfiFilesToKeep: string[] = [];
      for (const value of Object.values(runParameters)) {
        const pmtilesCache = new PMTilesCache(Filesystem);
        pmtilesCache.loadHFIPMTiles(
          DateTime.fromISO(value.for_date),
          value.run_type,
          DateTime.fromISO(value.run_datetime),
          "hfi.pmtiles",
        );
        hfiFilesToKeep.push(
          pmtilesCache.getHFIFileName(
            value.for_date,
            value.run_type,
            value.run_datetime,
            "hfi.pmtiles",
          ),
        );
      }
      clearStaleHFIPMTiles(Filesystem, hfiFilesToKeep);
    }
  }, [runParameters]);

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
        flexDirection: isPortrait || !isSmallScreen ? "column" : "row",
        overflow: "hidden",
        paddingBottom:
          isPortrait || !isSmallScreen ? "env(safe-area-inset-bottom)" : 0,
        backgroundColor:
          isPortrait || !isSmallScreen ? theme.palette.primary.main : "inherit",
      }}
    >
      {/* Show SideNavigation only in landscape and small screen */}
      {!isPortrait && isSmallScreen && (
        <SideNavigation tab={tab} setTab={setTab} />
      )}

      {/* Show AppHeader in portrait OR landscape with medium or larger screen */}
      {(isPortrait || !isSmallScreen) && <AppHeader />}

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
            date={dateOfInterest}
            setDate={setDateOfInterest}
            setTab={setTab}
            testId="asa-go-map"
          />
        </TabPanel>
        <TabPanel value={tab} panel={NavPanel.PROFILE}>
          <Profile
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
            date={dateOfInterest}
            setDate={setDateOfInterest}
            selectedFireCenter={fireCenter}
            setSelectedFireCenter={setFireCenter}
            selectedFireZoneUnit={selectedFireShape}
            setSelectedFireZoneUnit={setSelectedFireShape}
          />
        </TabPanel>
      </Box>

      {/* Show BottomNavigation in portrait OR landscape with medium or larger screen */}
      {(isPortrait || !isSmallScreen) && (
        <BottomNavigationBar tab={tab} setTab={setTab} />
      )}
    </Box>
  );
};

export default App;
