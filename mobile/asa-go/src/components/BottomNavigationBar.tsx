import { NavPanel } from "@/utils/constants";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import MapIcon from "@mui/icons-material/Map";
import SettingsIcon from "@mui/icons-material/Settings";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import {
  BottomNavigation,
  BottomNavigationAction,
  styled,
} from "@mui/material";

const StyledBottomNavigationAction = styled(BottomNavigationAction)(
  ({ theme }) => ({
    color: theme.palette.primary.contrastText,
    "&.Mui-selected": {
      color: theme.palette.secondary.main,
    },
    [theme.breakpoints.up("md")]: {
      paddingTop: theme.spacing(1),
      paddingBottom: theme.spacing(1),
      "& .MuiSvgIcon-root": {
        fontSize: "2.5rem",
      },
      "& .MuiBottomNavigationAction-label": {
        fontSize: "1rem",
        "&.Mui-selected": {
          fontSize: "1rem",
        },
      },
    },
  }),
);

interface BottomNavigationBarProps {
  tab: NavPanel;
  setTab: (newValue: NavPanel) => void;
}

const BottomNavigationBar = ({ tab, setTab }: BottomNavigationBarProps) => {
  return (
    <BottomNavigation
      showLabels
      value={tab}
      onChange={(
        _: React.SyntheticEvent<Element, Event>,
        newValue: NavPanel,
      ) => {
        setTab(newValue);
      }}
      sx={(theme) => ({
        backgroundColor: theme.palette.primary.main,
        color: theme.palette.primary.contrastText,
        py: theme.spacing(1),
        [theme.breakpoints.up("md")]: {
          minHeight: theme.spacing(8),
        },
      })}
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
      <StyledBottomNavigationAction
        aria-label={NavPanel.SETTINGS}
        label={NavPanel.SETTINGS}
        icon={<SettingsIcon />}
        value={NavPanel.SETTINGS}
      />
    </BottomNavigation>
  );
};

export default BottomNavigationBar;
