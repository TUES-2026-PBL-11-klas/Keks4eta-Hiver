import React from "react";
import { StyleSheet, Text, View } from "react-native";

interface SectionCardProps {
  title: string;
  description: string;
}

export const SectionCard = ({ title, description }: SectionCardProps) => (
  <View style={styles.card}>
    <Text style={styles.cardTitle}>{title}</Text>
    <Text style={styles.cardDescription}>{description}</Text>
  </View>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 16,
    padding: 20,
    marginVertical: 10,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8
  },
  cardDescription: {
    fontSize: 14,
    lineHeight: 22,
    color: "#4b5563"
  }
});
