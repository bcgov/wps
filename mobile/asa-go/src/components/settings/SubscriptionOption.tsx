import { FireZoneUnit } from "@/api/fbaAPI";
import { saveSubscriptions } from "@/slices/settingsSlice";
import { AppDispatch, selectSettings } from "@/store";
import { nameFormatter } from "@/utils/stringUtils";
import { ListItem, Typography, Switch } from "@mui/material";
import { useDispatch, useSelector } from "react-redux";

interface SubscriptionOptionProps {
  fireZoneUnit: FireZoneUnit;
}

const SubscriptionOption = ({ fireZoneUnit }: SubscriptionOptionProps) => {
  const dispatch: AppDispatch = useDispatch();
  const { subscriptions } = useSelector(selectSettings);

  // Toggles when the user taps the switch
  const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let newSubs: number[];
    if (e.target.checked) {
      newSubs = [...subscriptions, fireZoneUnit.id];
    } else {
      newSubs = subscriptions.filter((sub) => sub !== fireZoneUnit.id);
    }
    dispatch(saveSubscriptions(newSubs));
  };

  return (
    <ListItem
      secondaryAction={
        <Switch
          edge="end"
          checked={subscriptions.includes(fireZoneUnit.id)}
          onChange={handleSwitchChange}
          inputProps={{
            "aria-label": `Toggle subscription for ${fireZoneUnit.name}`,
          }}
        />
      }
      disableGutters
    >
      <Typography variant="body2" fontWeight="bold">
        {nameFormatter(fireZoneUnit.name, "Fire Zone", false)}
      </Typography>
    </ListItem>
  );
};

export default SubscriptionOption;
