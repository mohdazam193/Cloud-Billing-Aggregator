import { useState } from "react";
import axios from "axios";

export default function CloudCredentials({ onConnected }) {
  const [aws, setAws] = useState({});
  const [azure, setAzure] = useState({});

  return (
    <div className="p-6">
      <button onClick={async () => {
        await axios.post("/api/cloud/login",{aws,azure});
        onConnected();
      }}>Connect Cloud</button>
    </div>
  );
}
