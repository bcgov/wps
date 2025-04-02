import { theme } from "@/theme";
import { BottomNavigation, BottomNavigationAction, styled } from "@mui/material";
import MapIcon from "@mui/icons-material/Map";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import { NavPanel } from "@/utils/constants";

const StyledBottomNavigationAction = styled(BottomNavigationAction)({
  color: theme.palette.primary.contrastText,
  '&.Mui-selected': {
    color: theme.palette.secondary.main
  }
})

interface BottomNavigationBarProps {
  location: NavPanel
  setLocation: (newValue: NavPanel) => void
}

const BottomNavigationBar = ({location, setLocation}: BottomNavigationBarProps) => {
  return (
      <BottomNavigation
      showLabels
      value={location}
      onChange={(
        event: React.SyntheticEvent<Element, Event>,
        newValue: NavPanel
      ) => {
        setLocation(newValue);
      }}
      sx={{
        backgroundColor: theme.palette.primary.main,
        color: theme.palette.primary.contrastText,
      }}
    >
      <StyledBottomNavigationAction
        aria-label={NavPanel.MAP}
        label={NavPanel.MAP}
        icon={<MapIcon />}
        value={NavPanel.MAP}
      />
      <StyledBottomNavigationAction
        aria-label={NavPanel.PROFILE}
        label={NavPanel.PROFILE}
        icon={<AnalyticsIcon />}
        value={NavPanel.PROFILE}
      />
      <StyledBottomNavigationAction
        aria-label={NavPanel.ADVISORY}
        label={NavPanel.ADVISORY}
        icon={<TextSnippetIcon />}
        value={NavPanel.ADVISORY}
      />
    </BottomNavigation>
  )
}

export default BottomNavigationBar