import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function BlurTabBarBackground() {
  return (
    <View
      // System chrome material automatically adapts to the system's theme
      // and matches the native tab bar appearance on iOS.
      style={StyleSheet.absoluteFill}
    />
  );
}

export function useBottomTabOverflow() {
  const tabHeight = useBottomTabBarHeight();
  const { bottom } = useSafeAreaInsets();
  return tabHeight - bottom;
}
