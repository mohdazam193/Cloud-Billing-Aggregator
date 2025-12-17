import { useState } from "react";
import axios from "axios";
import Login from "./Login";
import CloudCredentials from "./CloudCredentials";
import Dashboard from "./Dashboard";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [connected, setConnected] = useState(false);
  const [summary, setSummary] = useState({});

  const load = async () => {
    setSummary((await axios.get("/api/summary")).data);
  };

  if (!loggedIn) return <Login onLogin={() => setLoggedIn(true)} />;
  if (!connected) return <CloudCredentials onConnected={() => { setConnected(true); load(); }} />;
  return <Dashboard summary={summary} />;
}
