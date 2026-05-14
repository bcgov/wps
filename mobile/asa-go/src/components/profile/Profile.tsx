import { FireShape } from "@/api/fbaAPI";
import type { FireCentre } from "@/types/fireCentre";
import FireCenterDropdown from "@/components/FireCenterDropdown";
import FireZoneUnitSummary from "@/components/profile/FireZoneUnitSummary";
import FireZoneUnitTabs from "@/components/report/FireZoneUnitTabs";
import TodayTomorrowSwitch from "@/components/TodayTomorrowSwitch";
import { selectFireCentres } from "@/store";
import { Box, useTheme } from "@mui/material";
import { DateTime } from "luxon";
import { useSelector } from "react-redux";

export interface ProfileProps {
  date: DateTime;
  setDate: React.Dispatch<React.SetStateAction<DateTime>>;
  selectedFireCentre: FireCentre | undefined;
  setSelectedFireCentre: React.Dispatch<
    React.SetStateAction<FireCentre | undefined>
  >;
  selectedFireZoneUnit: FireShape | undefined;
  setSelectedFireZoneUnit: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
}

const Profile = ({
  date,
  setDate,
  selectedFireCentre,
  setSelectedFireCentre,
  selectedFireZoneUnit,
  setSelectedFireZoneUnit,
}: ProfileProps) => {
  const { fireCentres } = useSelector(selectFireCentres);
  const theme = useTheme();
  return (
    <Box
      data-testid="asa-go-profile"
      sx={{
        display: "flex",
        flex: 1,
        flexDirection: "column",
        height: "100%",
        overflowY: "hidden",
      }}
    >
      <Box
        data-testid="profile-control-container"
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
          <TodayTomorrowSwitch border={true} date={date} setDate={setDate} />
        </Box>
        <Box sx={{ display: "flex", flexGrow: 1, pt: theme.spacing(1) }}>
          <FireCenterDropdown
            fireCentreOptions={fireCentres ?? []}
            selectedFireCentre={selectedFireCentre}
            setSelectedFireCentre={setSelectedFireCentre}
            setSelectedFireShape={setSelectedFireZoneUnit}
          />
        </Box>
      </Box>

      <Box
        id="profile-content-container"
        sx={{
          backgroundColor: "#FFFFFF",
          display: "flex",
          flexGrow: 1,
          paddingTop: theme.spacing(1),
          overflowY: "hidden",
        }}
      >
        <FireZoneUnitTabs
          selectedFireCentre={selectedFireCentre}
          selectedFireZoneUnit={selectedFireZoneUnit}
          setSelectedFireZoneUnit={setSelectedFireZoneUnit}
          date={date}
        >
          <FireZoneUnitSummary
            selectedFireCentre={selectedFireCentre}
            selectedFireZoneUnit={selectedFireZoneUnit}
            date={date}
          />
        </FireZoneUnitTabs>
      </Box>
    </Box>
  );
};

export default Profile;
