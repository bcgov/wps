import { useState } from "react";
import { Box } from "@mui/material";

import { DateTime } from "luxon";
import FBAMap from "@/FBAMap";
import { FireCenter, FireShape, RunType } from "@/api/fbaAPI";
import { PST_UTC_OFFSET } from "@/utils/constants";
import { AppHeader } from "@/AppHeader";
import { ASATabs } from "@/ASATabs";

const App = () => {
  const [fireCenter] = useState<FireCenter | undefined>(undefined);

  const [selectedFireShape, setSelectedFireShape] = useState<
    FireShape | undefined
  >(undefined);
  const [zoomSource, setZoomSource] = useState<
    "fireCenter" | "fireShape" | undefined
  >("fireCenter");
  const [dateOfInterest] = useState(
    DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).hour < 13
      ? DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
      : DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).plus({ days: 1 })
  );
  const [runType] = useState(RunType.FORECAST);

  return (
    <Box
      sx={{
        height: "100vh",
        padding: 0,
        margin: 0,
        width: 1024,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <AppHeader />
      <FBAMap
        selectedFireCenter={fireCenter}
        selectedFireShape={selectedFireShape}
        forDate={dateOfInterest}
        setSelectedFireShape={setSelectedFireShape}
        fireShapeAreas={[]}
        runType={runType}
        zoomSource={zoomSource}
        advisoryThreshold={0}
        setZoomSource={setZoomSource}
      />
      <ASATabs />
    </Box>
  );
};

export default App;
