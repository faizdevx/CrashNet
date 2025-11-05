import { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import * as L from "leaflet";
import "leaflet.heat";
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import axios from "axios";
import "./App.css";

const WS_URL = "ws://localhost:8002/ws";
const SUMMARY_URL = "http://localhost:8000/summary";
const HEALTH_URL = "http://localhost:8001/health";

// helper component to add/remove heat layer imperatively
function HeatLayer({ points }) {
  const map = useMap();
  const layerRef = useRef(null);

  useEffect(() => {
    if (!map) return;
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
      layerRef.current = null;
    }
    if (points.length > 0) {
      // points: [[lat, lon, intensity], ...]
      layerRef.current = L.heatLayer(points, { radius: 25, blur: 20, maxZoom: 16 }).addTo(map);
    }
    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
        layerRef.current = null;
      }
    };
  }, [map, points]);

  return null;
}

export default function App() {
  const [events, setEvents] = useState([]); // raw events (recent)
  const [heatPoints, setHeatPoints] = useState([]); // for heatmap
  const [chartData, setChartData] = useState([]); // confidence over time
  const [summary, setSummary] = useState({});
  const [health, setHealth] = useState({});
  const maxWindow = 600; // events to keep

  // open WS
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => console.log("WS open");
    ws.onmessage = (msg) => {
      try {
        const d = JSON.parse(msg.data);
        // expecting { id, coords: [lat, lon], accident: bool, score: num, ts? }
        const ev = {
          id: d.id || d.device_id || Math.random().toString(36).slice(2,8),
          lat: (d.coords && d.coords[0]) || d.lat || 0,
          lon: (d.coords && d.coords[1]) || d.lon || 0,
          accident: !!d.accident,
          score: typeof d.score === "number" ? d.score : (d.details && d.details.score) || 0,
          ts: d.ts ? new Date(d.ts * 1000) : new Date(),
        };
        setEvents(prev => {
          const next = [ev, ...prev].slice(0, maxWindow);
          // update heatPoints: weight accidents higher
          const heat = next.map(e => [e.lat, e.lon, e.accident ? 1.5 : Math.max(0.2, Math.min(1, (Math.abs(e.score)+1)/10))]);
          setHeatPoints(heat);
          // update chart
          setChartData(prevChart => {
            const newPoint = { ts: ev.ts.toLocaleTimeString(), score: Math.round(ev.score*100)/100 };
            return [...prevChart.slice(-99), newPoint];
          });
          return next;
        });
      } catch (e) {
        console.error("ws parse", e, msg.data);
      }
    };
    ws.onclose = () => console.log("WS closed");
    return () => ws.close();
  }, []);

  // poll summary + health
  useEffect(() => {
    let mounted = true;
    async function poll() {
      try {
        const [sRes, hRes] = await Promise.allSettled([axios.get(SUMMARY_URL), axios.get(HEALTH_URL)]);
        if (!mounted) return;
        if (sRes.status === "fulfilled") setSummary(sRes.value.data);
        if (hRes.status === "fulfilled") setHealth(hRes.value.data);
      } catch (e) {
        console.error(e);
      }
    }
    poll();
    const id = setInterval(poll, 2000);
    return () => { mounted = false; clearInterval(id); };
  }, []);

  const center = [26.8467, 80.9462]; // default view (Lucknow)

  return (
    <div style={{ fontFamily: "Inter, Arial, sans-serif" }}>
      <header style={{ padding: "8px 16px", background: "#0f1724", color: "#fff", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>CrashNet Live Dashboard</h2>
        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ background: "#111827", padding: "8px 12px", borderRadius: 8 }}>
            <div style={{ fontSize: 12, color: "#9ca3af" }}>Model loaded</div>
            <div style={{ fontWeight: 700, color: health.model_loaded ? "#34d399" : "#fb7185" }}>{String(health.model_loaded)}</div>
          </div>
          <div style={{ background: "#111827", padding: "8px 12px", borderRadius: 8 }}>
            <div style={{ fontSize: 12, color: "#9ca3af" }}>Window size</div>
            <div style={{ fontWeight: 700 }}>{events.length}</div>
          </div>
          <div style={{ background: "#111827", padding: "8px 12px", borderRadius: 8 }}>
            <div style={{ fontSize: 12, color: "#9ca3af" }}>Recent accidents</div>
            <div style={{ fontWeight: 700 }}>{summary.recent_accidents ?? 0}</div>
          </div>
        </div>
      </header>

      <main style={{ padding: 12 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 12 }}>
          {/* Map + heat */}
          <div style={{ background: "#fff", borderRadius: 8, overflow: "hidden", minHeight: 500 }}>
            <MapContainer center={center} zoom={10} style={{ height: 520, width: "100%" }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <HeatLayer points={heatPoints} />
              {events.slice(0, 200).map((e, i) => (
                <CircleMarker
                  key={i}
                  center={[e.lat, e.lon]}
                  radius={e.accident ? 8 : 4}
                  pathOptions={{ color: e.accident ? "#e11d48" : "#10b981", fillOpacity: 0.8 }}
                >
                  <Popup>
                    <div><strong>id</strong>: {e.id}</div>
                    <div><strong>score</strong>: {e.score}</div>
                    <div><strong>ts</strong>: {e.ts.toLocaleTimeString()}</div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>

          {/* Right column: charts + list */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ background: "#fff", padding: 12, borderRadius: 8 }}>
              <h4 style={{ margin: "0 0 8px 0" }}>Model Confidence Over Time</h4>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={chartData}>
                  <Line type="monotone" dataKey="score" stroke="#ef4444" dot={false} />
                  <CartesianGrid stroke="#eee" />
                  <XAxis dataKey="ts" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div style={{ background: "#fff", padding: 12, borderRadius: 8 }}>
              <h4 style={{ margin: "0 0 8px 0" }}>Summary</h4>
              <div><strong>Total messages:</strong> {summary.total ?? 0}</div>
              <div><strong>Avg speed:</strong> {(summary.avg_speed ?? 0).toFixed(1)}</div>
              <div><strong>Recent accidents:</strong> {summary.recent_accidents ?? 0}</div>
            </div>

            <div style={{ background: "#fff", padding: 12, borderRadius: 8, overflow: "auto", height: 220 }}>
              <h4 style={{ margin: "0 0 8px 0" }}>Recent Alerts (most recent first)</h4>
              {events.slice(0, 200).map((e, i) => (
                <div key={i} style={{ borderBottom: "1px solid #eee", padding: "6px 0" }}>
                  <div style={{ fontWeight: 700 }}>
                    {e.accident ? "⚠ Accident" : "Normal"} — {e.id}
                  </div>
                  <div style={{ fontSize: 12, color: "#555" }}>
                    score: {e.score} • {e.ts.toLocaleTimeString()} • {e.lat.toFixed(4)},{e.lon.toFixed(4)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <footer style={{ marginTop: 16, color: "#666", fontSize: 13 }}>
          CrashNet · Live simulation · Local demo
        </footer>
      </main>
    </div>
  );
}
