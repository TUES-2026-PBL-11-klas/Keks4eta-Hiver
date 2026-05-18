import React from "react";
import { StyleSheet, Text, View } from "react-native";

interface BrandHeaderProps {
  title: string;
  subtitle?: string;
}

export const BrandHeader = ({ title, subtitle }: BrandHeaderProps) => (
  <View style={styles.header}>
    <Text style={styles.title}>{title}</Text>
    {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
  </View>
);

const styles = StyleSheet.create({
  header: {
    marginVertical: 24,
    paddingHorizontal: 16
  },
  title: {
    fontSize: 32,
    fontWeight: "700",
    color: "#111827"
  },
  subtitle: {
    marginTop: 6,
    color: "#6b7280",
    fontSize: 16
  }
});
