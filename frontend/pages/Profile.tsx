import React from "react";
import { StyleSheet, Text, View } from "react-native";

const Profile = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Profile</Text>
    <Text style={styles.body}>This page is a placeholder for account and user settings.</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    justifyContent: "center",
    alignItems: "center"
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 12
  },
  body: {
    fontSize: 16,
    color: "#6b7280",
    textAlign: "center"
  }
});

export default Profile;
