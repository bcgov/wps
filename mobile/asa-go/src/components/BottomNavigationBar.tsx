import { useIsTablet } from "@/hooks/useIsTablet";
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

const StyledBottomNavigation = styled(BottomNavigation)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  paddingTop: theme.spacing(1),
  paddingBottom: theme.spacing(1),
  minHeight: theme.spacing(8),
  [theme.breakpoints.up("md")]: {
    minHeight: theme.spacing(9),
  },
}));

const StyledBottomNavigationAction = styled(BottomNavigationAction)(
  ({ theme }) => ({
    color: theme.palette.primary.contrastText,
    paddingTop: theme.spacing(1),
    paddingBottom: theme.spacing(1),
    "&.Mui-selected": {
      color: theme.palette.secondary.main,
    },
    [theme.breakpoints.up("md")]: {
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
  const isTablet = useIsTablet();
  const actionIconSx = {
    fontSize: isTablet ? 40 : 32,
  };

  return (
    <StyledBottomNavigation
      showLabels
      value={tab}
      onChange={(
        _: React.SyntheticEvent<Element, Event>,
        newValue: NavPanel,
      ) => {
        setTab(newValue);
      }}
    >
      <StyledBottomNavigationAction
        aria-label={NavPanel.MAP}
        label={NavPanel.MAP}
        icon={<MapIcon sx={actionIconSx} />}
        value={NavPanel.MAP}
      />
      <StyledBottomNavigationAction
        aria-label={NavPanel.PROFILE}
        label={NavPanel.PROFILE}
        icon={<AnalyticsIcon sx={actionIconSx} />}
        value={NavPanel.PROFILE}
      />
      <StyledBottomNavigationAction
        aria-label={NavPanel.ADVISORY}
        label={NavPanel.ADVISORY}
        icon={<TextSnippetIcon sx={actionIconSx} />}
        value={NavPanel.ADVISORY}
      />
      <StyledBottomNavigationAction
        aria-label={NavPanel.SETTINGS}
        label={NavPanel.SETTINGS}
        icon={<SettingsIcon sx={actionIconSx} />}
        value={NavPanel.SETTINGS}
      />
    </StyledBottomNavigation>
  );
};

export default BottomNavigationBar;
