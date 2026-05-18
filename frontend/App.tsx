import { StatusBar } from "expo-status-bar";
import React from "react";
import { SafeAreaView, StyleSheet, View } from "react-native";
import Home from "./pages/Home";
import { BrandHeader } from "./components/BrandHeader";

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <BrandHeader title="Hiver" subtitle="Mobile + Web starter" />
      <View style={styles.content}>
        <Home />
      </View>
      <StatusBar style="auto" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc"
  },
  content: {
    flex: 1,
    padding: 16
  }
});
