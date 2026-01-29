import React, { useState } from "react";
import { View, Text, TextInput, Button, StyleSheet } from "react-native";
import * as LocalAuthentication from "expo-local-authentication";

export default function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("Idle");

  const handleBiometric = async () => {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    if (!hasHardware) {
      setStatus("Biometria indisponivel");
      return;
    }
    const result = await LocalAuthentication.authenticateAsync();
    setStatus(result.success ? "Biometria OK" : "Biometria falhou");
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>LuisBank Mobile</Text>
      <TextInput style={styles.input} placeholder="Email" value={email} onChangeText={setEmail} />
      <TextInput
        style={styles.input}
        placeholder="Senha"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Button title="Login (demo)" onPress={() => setStatus("Login enviado")} />
      <View style={{ height: 12 }} />
      <Button title="Biometria" onPress={handleBiometric} />
      <Text style={styles.status}>{status}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { fontSize: 20, marginBottom: 16, textAlign: "center" },
  input: { borderWidth: 1, borderColor: "#ccc", marginBottom: 12, padding: 8 },
  status: { marginTop: 16, textAlign: "center" },
});
