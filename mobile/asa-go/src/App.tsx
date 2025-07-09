import { useEffect, useState } from "react";
import { Box } from "@mui/material";

import FBAMap from "@/components/map/FBAMap";
import { FireCenter, FireShape } from "@/api/fbaAPI";
import { AppHeader } from "@/components/AppHeader";
import { useDispatch, useSelector } from "react-redux";
import { DateTime } from "luxon";
import { NavPanel, PST_UTC_OFFSET } from "@/utils/constants";
import { selectFireCenters, selectRunParameter, AppDispatch } from "@/store";
import { isNull, isUndefined } from "lodash";
import { fetchMostRecentSFMSRunParameter } from "@/slices/runParameterSlice";
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

const HFI_THRESHOLD = 20;

const App = () => {
  const dispatch: AppDispatch = useDispatch();
  const { fireCenters } = useSelector(selectFireCenters);
  const [tab, setTab] = useState<NavPanel>(NavPanel.MAP);
  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(
    undefined
  );
  const [selectedFireShape] = useState<FireShape | undefined>(undefined);
  const [zoomSource] = useState<"fireCenter" | "fireShape" | undefined>(
    "fireCenter"
  );
  const [dateOfInterest, setDateOfInterest] = useState(
    DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
  );
  const { runDatetime, runType } = useSelector(selectRunParameter);

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
      dispatch(fetchMostRecentSFMSRunParameter(doiISODate));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate();
    if (!isNull(doiISODate)) {
      dispatch(fetchMostRecentSFMSRunParameter(doiISODate));
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
      !isNull(runDatetime) &&
      !isNull(doiISODate) &&
      !isUndefined(runDatetime) &&
      !isUndefined(fireCenter) &&
      !isNull(fireCenter) &&
      !isNull(runType)
    ) {
      dispatch(
        fetchFireCentreTPIStats(
          fireCenter.name,
          runType,
          doiISODate,
          runDatetime
        )
      );
      dispatch(
        fetchFireCentreHFIFuelStats(
          fireCenter.name,
          runType,
          doiISODate,
          runDatetime
        )
      );
    }
  }, [fireCenter, runDatetime]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate();
    if (!isNull(doiISODate) && !isNull(runType)) {
      dispatch(fetchFireShapeAreas(runType, runDatetime, doiISODate));
      dispatch(fetchProvincialSummary(runType, runDatetime, doiISODate));
    }
  }, [runDatetime]); // eslint-disable-line react-hooks/exhaustive-deps

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
      {tab === NavPanel.MAP && (
        <FBAMap
          selectedFireCenter={fireCenter}
          selectedFireShape={selectedFireShape}
          zoomSource={zoomSource}
          advisoryThreshold={HFI_THRESHOLD}
          date={dateOfInterest}
          setDate={setDateOfInterest}
        />
      )}
      {tab === NavPanel.PROFILE && <Profile />}
      {tab === NavPanel.ADVISORY && <Advisory />}
      <BottomNavigationBar tab={tab} setTab={setTab} />
    </Box>
  );
};

export default App;
