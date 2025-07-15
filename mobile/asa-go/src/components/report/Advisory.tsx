import { FireCenter, FireShape } from "@/api/fbaAPI";
import FireCenterDropdown from "@/components/FireCenterDropdown";
import FireZoneUnitTabs from "@/components/report/FireZoneUnitTabs";
import TodayTomorrowSwitch from "@/components/TodayTomorrowSwitch";
import { selectFireCenters } from "@/store";
import { INFO_PANEL_CONTENT_BACKGROUND, LIGHT_GREY } from "@/theme";
import { Box, FormControl, useTheme } from "@mui/material";
import { DateTime } from "luxon";
import { useSelector } from "react-redux";

interface AdvisoryProps {
  advisoryThreshold: number;
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
  advisoryThreshold,
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
      }}
    >
      <Box
        sx={{
          alignItems: "center",
          backgroundColor: LIGHT_GREY,
          display: "flex",
          padding: theme.spacing(1),
        }}
      >
        <Box sx={{ display: "flex", flexGrow: 1, pt: theme.spacing(1) }}>
          <FormControl
            sx={{ backgroundColor: "white", margin: 1, minWidth: 280 }}
          >
            <FireCenterDropdown
              fireCenterOptions={fireCenters}
              selectedFireCenter={selectedFireCenter}
              setSelectedFireCenter={setSelectedFireCenter}
              setSelectedFireShape={setSelectedFireZoneUnit}
            />
          </FormControl>
        </Box>
        <Box
          sx={{ alignItems: "center", display: "flex", pr: theme.spacing(1) }}
        >
          <TodayTomorrowSwitch date={date} setDate={setDate} />
        </Box>
      </Box>
      <Box
        sx={{
          backgroundColor: INFO_PANEL_CONTENT_BACKGROUND,
          display: "flex",
          flexGrow: 1,
        }}
      >
        <FireZoneUnitTabs
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={selectedFireCenter}
          selectedFireZoneUnit={selectedFireZoneUnit}
          setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        />
      </Box>
    </Box>
  );
};

export default Advisory;
