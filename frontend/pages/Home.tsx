import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SectionCard } from "../components/SectionCard";

const Home = () => {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.section}>
        <Text style={styles.heading}>Welcome to Hiver</Text>
        <Text style={styles.body}>A shared frontend starter for web and mobile.</Text>
      </View>
      <SectionCard
        title="Cross-platform UI"
        description="Build screens once and run them on iOS, Android, and web using React Native and Expo."
      />
      <SectionCard
        title="Backend-ready"
        description="Integrate with your Node.js / Django APIs via shared hooks and lib utilities."
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    paddingBottom: 40
  },
  section: {
    marginBottom: 24
  },
  heading: {
    fontSize: 26,
    fontWeight: "700",
    color: "#111827"
  },
  body: {
    marginTop: 8,
    fontSize: 16,
    color: "#4b5563",
    lineHeight: 24
  }
});

export default Home;
