import { useState } from "react";
import axios from "axios";

export default function Login({ onLogin }) {
  const [u, setU] = useState("");
  const [p, setP] = useState("");

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="p-6 bg-white shadow">
        <input placeholder="Username" onChange={e => setU(e.target.value)} />
        <input type="password" placeholder="Password" onChange={e => setP(e.target.value)} />
        <button onClick={async () => {
          await axios.post("/api/auth/login",{username:u,password:p});
          onLogin();
        }}>Login</button>
      </div>
    </div>
  );
}
