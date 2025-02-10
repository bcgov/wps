import { useState } from "react";
import { Box } from "@mui/material";

import FBAMap from "@/FBAMap";
import { FireCenter, FireShape } from "@/api/fbaAPI";
import { AppHeader } from "@/components/AppHeader";
import { ASATabs } from "@/components/ASATabs";

const App = () => {
  const [fireCenter] = useState<FireCenter | undefined>(undefined);

  const [selectedFireShape] = useState<FireShape | undefined>(undefined);
  const [zoomSource] = useState<"fireCenter" | "fireShape" | undefined>(
    "fireCenter"
  );

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
        fireShapeAreas={[]}
        zoomSource={zoomSource}
        advisoryThreshold={0}
      />
      <ASATabs />
    </Box>
  );
};

export default App;
