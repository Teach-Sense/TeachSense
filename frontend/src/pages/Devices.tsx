import { useEffect, useState } from "react";
import { Loader2, Plus, Cpu, Wifi, WifiOff, RefreshCw, Copy, Check } from "lucide-react";
import DashboardLayout from "../layouts/DashboardLayout";
import api from "../services/api";

type Device = {
  id: number;
  name: string;
  type: string;
  protocol: string;
  status?: string;
  last_seen?: string;
  last_heartbeat?: string;
};

// Generates a reasonably strong random key for the device to authenticate
// its hardware WebSocket connection with. Devices themselves don't log in
// with a user password — this key is what they present instead.
const generateDeviceKey = () => {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
};

const Devices = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncUnavailable, setSyncUnavailable] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState("audio_input");
  const [protocol, setProtocol] = useState("websocket");
  const [deviceKey, setDeviceKey] = useState(generateDeviceKey());
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  // Holds the auth_token returned right after registering a device, so the
  // user can copy it onto the Arduino/ESP32. This is only ever shown once —
  // the backend won't return it again on later GETs.
  const [justRegistered, setJustRegistered] = useState<{
    name: string;
    authToken: string;
    wsUrl?: string;
  } | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchDevices = async () => {
    try {
      const { data } = await api.get("/api/devices/");
      const list = data.data?.results ?? data.results ?? data;
      setDevices(Array.isArray(list) ? list : []);
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
    } catch (err: any) {
      // This endpoint isn't confirmed to exist on the backend yet.
      // Don't block the page on it — just refresh the list instead,
      // and stop showing the button once we know it's not there.
      if (err?.response?.status === 404) {
        setSyncUnavailable(true);
      }
      await fetchDevices();
    } finally {
      setSyncing(false);
    }
  };

  const registerDevice = async () => {
    if (!name.trim()) return;
    setCreating(true);
    setError("");
    setJustRegistered(null);
    try {
      const { data } = await api.post("/api/devices/", {
        name,
        type,
        protocol,
        device_key: deviceKey,
      });
      const result = data.data ?? data;

      setJustRegistered({
        name: result.name ?? name,
        authToken: result.auth_token,
        wsUrl: result.ws_url,
      });

      setName("");
      setDeviceKey(generateDeviceKey());
      fetchDevices();
    } catch (err: any) {
      const errors = err?.response?.data?.errors;
      const detail =
        (errors && Object.entries(errors).map(([k, v]) => `${k}: ${(v as string[]).join(", ")}`).join(" | ")) ||
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        "Failed to register device.";
      setError(detail);
    } finally {
      setCreating(false);
    }
  };

  const copyAuthToken = async () => {
    if (!justRegistered?.authToken) return;
    await navigator.clipboard.writeText(justRegistered.authToken);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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

  // Backend has used both "connected"/"disconnected"/"pending" (from docs)
  // and possibly "online"/"offline" depending on version — treat both as
  // equivalent so the badge doesn't silently look wrong either way.
  const isOnline = (status?: string) =>
    status === "online" || status === "connected" || status === "active";

  return (
    <DashboardLayout title="Devices">
      <div className="max-w-4xl mx-auto space-y-6 sm:space-y-8">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Hardware Devices</h1>
            <p className="text-sm text-gray-400 mt-1">Manage classroom microphones and audio devices</p>
          </div>
          {!syncUnavailable && (
            <button
              onClick={syncDevices}
              disabled={syncing}
              className="flex items-center justify-center gap-2 border border-[#5cce6a]/30 text-[#2d9e3c] px-4 py-2 rounded-xl text-sm font-medium hover:bg-[#f0fdf4] transition w-full sm:w-auto"
            >
              <RefreshCw size={14} className={syncing ? "animate-spin" : ""} />
              Sync Devices
            </button>
          )}
        </div>

        {/* Register Device */}
        <div className="bg-white border border-gray-100 rounded-2xl p-4 sm:p-6 shadow-sm">
          <h2 className="text-xs font-mono uppercase tracking-widest text-gray-400 mb-4">
            Register New Device
          </h2>

          {error && (
            <p className="text-red-500 text-sm mb-4 bg-red-50 border border-red-100 rounded-xl px-4 py-3 whitespace-pre-line">
              {error}
            </p>
          )}

          {justRegistered && (
            <div className="mb-4 bg-emerald-50 border border-emerald-200 rounded-xl p-4 space-y-2">
              <p className="text-sm font-semibold text-emerald-700">
                "{justRegistered.name}" registered — copy this auth token now, it won't be shown again.
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-white border border-emerald-100 rounded-lg px-3 py-2 text-xs font-mono text-gray-700 overflow-x-auto">
                  {justRegistered.authToken}
                </code>
                <button
                  onClick={copyAuthToken}
                  className="shrink-0 flex items-center gap-1 text-xs font-medium text-emerald-700 border border-emerald-200 rounded-lg px-3 py-2 hover:bg-emerald-100 transition"
                >
                  {copied ? <Check size={13} /> : <Copy size={13} />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
              {justRegistered.wsUrl && (
                <p className="text-xs text-emerald-600 font-mono break-all">{justRegistered.wsUrl}</p>
              )}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
            <input
              type="text"
              placeholder="Device name e.g. Classroom Mic"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={255}
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

          {/* device_key: required by the backend, but not something the
              user needs to think about — it's auto-generated and just
              shown here for transparency/debugging. */}
          <div className="mb-4">
            <label className="block text-xs text-gray-400 font-mono mb-1">
              Device Key (auto-generated, sent with registration)
            </label>
            <div className="flex gap-2">
              <code className="flex-1 border border-gray-200 rounded-xl px-4 py-2 text-xs font-mono text-gray-500 bg-gray-50 overflow-x-auto">
                {deviceKey}
              </code>
              <button
                type="button"
                onClick={() => setDeviceKey(generateDeviceKey())}
                className="shrink-0 text-xs font-medium text-gray-500 border border-gray-200 rounded-xl px-3 hover:bg-gray-50 transition"
                title="Generate a new key"
              >
                <RefreshCw size={13} />
              </button>
            </div>
          </div>

          <button
            onClick={registerDevice}
            disabled={creating || !name.trim()}
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-[#2d9e3c] to-[#5cce6a] text-white px-5 py-3 rounded-xl text-sm font-bold hover:from-[#3dae4c] hover:to-[#6cde7a] transition disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-green-200 w-full sm:w-auto"
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
                  className="bg-white border border-gray-100 rounded-2xl p-4 sm:p-5 shadow-sm hover:shadow-md hover:border-[#5cce6a]/20 transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div className="flex items-center gap-3 sm:gap-4">
                      <div className="w-10 h-10 bg-gradient-to-br from-[#e8fbed] to-[#c6f5d0] rounded-xl flex items-center justify-center shrink-0">
                        <Cpu size={16} className="text-[#2d9e3c]" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{device.name}</h3>
                        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
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

                    <div className="flex items-center gap-3 flex-wrap">
                      <div className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1 rounded-full ${
                        isOnline(device.status)
                          ? "bg-emerald-50 text-emerald-600"
                          : "bg-gray-100 text-gray-400"
                      }`}>
                        {isOnline(device.status) ? <Wifi size={11} /> : <WifiOff size={11} />}
                        {device.status || "offline"}
                      </div>

                      {(device.last_seen || device.last_heartbeat) && (
                        <p className="text-xs text-gray-400 font-mono">
                          Last seen: {new Date(device.last_seen || device.last_heartbeat!).toLocaleTimeString()}
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
        <div className="bg-gradient-to-br from-[#0d1f0f] to-[#071a09] rounded-2xl p-4 sm:p-6 text-white">
          <h2 className="text-xs font-mono uppercase tracking-widest text-[#5cce6a]/60 mb-3">
            Hardware Setup
          </h2>
          <p className="text-sm text-white/60 mb-4">
            To connect an Arduino or ESP32 device, use the WebSocket endpoint below,
            authenticating with the device's auth token shown after registration:
          </p>
          <div className="bg-black/30 rounded-xl p-3 sm:p-4 font-mono text-xs text-[#5cce6a] overflow-x-auto">
            wss://teachsense.up.railway.app/ws/devices/&#123;device_token&#125;/
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