import { useEffect, useState } from "react";
import { Loader2, Plus, Cpu, Wifi, WifiOff, RefreshCw, Trash2 } from "lucide-react";
import DashboardLayout from "../layouts/DashboardLayout";
import api from "../services/api";

type Device = {
  id: number;
  name: string;
  type: string;
  protocol: string;
  status?: string;
  last_seen?: string;
};

const Devices = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState("audio_input");
  const [protocol, setProtocol] = useState("websocket");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const fetchDevices = async () => {
    try {
      const { data } = await api.get("/api/devices/");
      setDevices(data);
    } catch {
      console.error("Failed to fetch devices");
    } finally {
      setLoading(false);
    }
  };

  const syncDevices = async () => {
    setSyncing(true);
    try {
      await api.post("/api/devices/sync/");
      await fetchDevices();
    } catch {
      console.error("Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const registerDevice = async () => {
    if (!name.trim()) return;
    setCreating(true);
    setError("");
    try {
      await api.post("/api/devices/", { name, type, protocol });
      setName("");
      fetchDevices();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to register device.");
    } finally {
      setCreating(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const deviceTypeLabel: Record<string, string> = {
    audio_input: "Audio Input",
    audio_output: "Audio Output",
    sensor: "Sensor",
    other: "Other",
  };

  return (
    <DashboardLayout title="Devices">
      <div className="max-w-4xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Hardware Devices</h1>
            <p className="text-sm text-gray-400 mt-1">Manage classroom microphones and audio devices</p>
          </div>
          <button
            onClick={syncDevices}
            disabled={syncing}
            className="flex items-center gap-2 border border-[#5cce6a]/30 text-[#2d9e3c] px-4 py-2 rounded-xl text-sm font-medium hover:bg-[#f0fdf4] transition"
          >
            <RefreshCw size={14} className={syncing ? "animate-spin" : ""} />
            Sync Devices
          </button>
        </div>

        {/* Register Device */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xs font-mono uppercase tracking-widest text-gray-400 mb-4">
            Register New Device
          </h2>

          {error && (
            <p className="text-red-500 text-sm mb-4 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
              {error}
            </p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
            <input
              type="text"
              placeholder="Device name e.g. Classroom Mic"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#5cce6a]/30 focus:border-[#5cce6a] transition"
            />
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#5cce6a]/30 focus:border-[#5cce6a] transition bg-white"
            >
              <option value="audio_input">Audio Input</option>
              <option value="audio_output">Audio Output</option>
              <option value="sensor">Sensor</option>
              <option value="other">Other</option>
            </select>
            <select
              value={protocol}
              onChange={(e) => setProtocol(e.target.value)}
              className="border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#5cce6a]/30 focus:border-[#5cce6a] transition bg-white"
            >
              <option value="websocket">WebSocket</option>
              <option value="http">HTTP</option>
              <option value="mqtt">MQTT</option>
            </select>
          </div>

          <button
            onClick={registerDevice}
            disabled={creating || !name.trim()}
            className="flex items-center gap-2 bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white px-5 py-3 rounded-xl text-sm font-bold hover:from-[#3dae4c] hover:to-[#6cde7a] transition disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-green-200"
          >
            {creating ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
            Register Device
          </button>
        </div>

        {/* Devices List */}
        <div>
          <h2 className="text-xs font-mono uppercase tracking-widest text-gray-400 mb-4">
            Registered Devices
          </h2>

          {loading ? (
            <div className="flex items-center justify-center py-16 text-gray-400">
              <Loader2 size={22} className="animate-spin mr-3" /> Loading devices...
            </div>
          ) : devices.length === 0 ? (
            <div className="bg-white border border-dashed border-gray-200 rounded-2xl py-16 text-center text-gray-400">
              <Cpu size={32} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">No devices registered yet.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {devices.map((device) => (
                <div
                  key={device.id}
                  className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md hover:border-[#5cce6a]/20 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-gradient-to-br from-[#e8fbed] to-[#c6f5d0] rounded-xl flex items-center justify-center shrink-0">
                        <Cpu size={16} className="text-[#2d9e3c]" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{device.name}</h3>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs text-gray-400 font-mono">
                            {deviceTypeLabel[device.type] || device.type}
                          </span>
                          <span className="text-gray-300">·</span>
                          <span className="text-xs text-gray-400 font-mono uppercase">
                            {device.protocol}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {/* Online/Offline status */}
                      <div className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1 rounded-full ${
                        device.status === "online"
                          ? "bg-emerald-50 text-emerald-600"
                          : "bg-gray-100 text-gray-400"
                      }`}>
                        {device.status === "online"
                          ? <Wifi size={11} />
                          : <WifiOff size={11} />
                        }
                        {device.status || "offline"}
                      </div>

                      {device.last_seen && (
                        <p className="text-xs text-gray-400 font-mono hidden sm:block">
                          Last seen: {new Date(device.last_seen).toLocaleTimeString()}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Hardware Setup Guide */}
        <div className="bg-gradient-to-br from-[#0d1f0f] to-[#071a09] rounded-2xl p-6 text-white">
          <h2 className="text-xs font-mono uppercase tracking-widest text-[#5cce6a]/60 mb-3">
            Hardware Setup
          </h2>
          <p className="text-sm text-white/60 mb-4">
            To connect an Arduino or ESP32 device, use the WebSocket endpoint:
          </p>
          <div className="bg-black/30 rounded-xl p-4 font-mono text-xs text-[#5cce6a] overflow-x-auto">
            wss://teachsense.onrender.com/ws/devices/&#123;device_id&#125;/
          </div>
          <p className="text-xs text-white/40 mt-3">
            See the hardware integration docs for the full Arduino code example.
          </p>
        </div>

      </div>
    </DashboardLayout>
  );
};

export default Devices;