import { FireCenter, FireShape } from "@/api/fbaAPI";
import FireCenterDropdown from "@/components/FireCenterDropdown";
import AdvisoryText from "@/components/report/AdvisoryText";
import FireZoneUnitTabs from "@/components/report/FireZoneUnitTabs";
import TodayTomorrowSwitch from "@/components/TodayTomorrowSwitch";
import { selectFireCenters } from "@/store";
import { Box, useTheme } from "@mui/material";
import { DateTime } from "luxon";
import { useSelector } from "react-redux";

interface AdvisoryProps {
  date: DateTime;
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
  selectedFireCenter: FireCenter | undefined;
  setSelectedFireCenter: React.Dispatch<
    React.SetStateAction<FireCenter | undefined>
  >;
  selectedFireZoneUnit: FireShape | undefined;
  setSelectedFireZoneUnit: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
}

const Advisory = ({
  date,
  setDate,
  selectedFireCenter,
  setSelectedFireCenter,
  selectedFireZoneUnit,
  setSelectedFireZoneUnit,
}: AdvisoryProps) => {
  const { fireCenters } = useSelector(selectFireCenters);
  const theme = useTheme();
  return (
    <Box
      data-testid="asa-go-advisory"
      sx={{
        display: "flex",
        flex: 1,
        flexDirection: "column",
        height: "100%",
      }}
    >
      <Box
        data-testid="advisory-control-container"
        sx={{
          alignItems: "end",
          backgroundColor: "white",
          display: "flex",
          padding: theme.spacing(1),
        }}
      >
        <Box
          sx={{ alignItems: "center", display: "flex", pr: theme.spacing(1) }}
        >
          <TodayTomorrowSwitch border date={date} setDate={setDate} />
        </Box>
        <Box sx={{ display: "flex", flexGrow: 1, pt: theme.spacing(1) }}>
          <FireCenterDropdown
            fireCenterOptions={fireCenters ?? []}
            selectedFireCenter={selectedFireCenter}
            setSelectedFireCenter={setSelectedFireCenter}
            setSelectedFireShape={setSelectedFireZoneUnit}
          />
        </Box>
      </Box>
      <Box
        id="advisory-content-container"
        sx={{
          backgroundColor: "#FFFFFF",
          display: "flex",
          flexGrow: 1,
          paddingTop: theme.spacing(1),
          overflowY: "hidden",
        }}
      >
        <FireZoneUnitTabs
          selectedFireCenter={selectedFireCenter}
          selectedFireZoneUnit={selectedFireZoneUnit}
          setSelectedFireZoneUnit={setSelectedFireZoneUnit}
          date={date}
        >
          <AdvisoryText
            selectedFireCenter={selectedFireCenter}
            selectedFireZoneUnit={selectedFireZoneUnit}
            date={date}
          />
        </FireZoneUnitTabs>
      </Box>
    </Box>
  );
};

export default Advisory;
