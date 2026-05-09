import React, { useState, useEffect } from 'react';
import axios from 'axios';
import MapComponent from './components/MapComponent';
import Dashboard from './components/Dashboard';
import { Navigation2 } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('Initializing...');
  const [mapData, setMapData] = useState(null);
  
  const [urgency, setUrgency] = useState(5);
  const [startNode, setStartNode] = useState(null);
  const [startNodeCoords, setStartNodeCoords] = useState(null);
  
  const [gaResult, setGaResult] = useState(null);
  const [baselineResult, setBaselineResult] = useState(null);
  
  // Initialization
  useEffect(() => {
    initSystem();
  }, []);

  const initSystem = async () => {
    try {
      setLoading(true);
      setStatusMsg('Downloading & Loading Map (Noida Sec 62)...');
      const res = await axios.get(`${API_BASE}/load_map`);
      setMapData(res.data);
      setStartNode(res.data.sample_start_node);
      setStartNodeCoords(res.data.sample_coords);
      setStatusMsg('Map Loaded Successfully.');
      setLoading(false);
    } catch (err) {
      console.error(err);
      setStatusMsg('Error loading map. Make sure backend is running.');
      setLoading(false);
    }
  };

  const simulateTraffic = async () => {
    try {
      setStatusMsg('Simulating new traffic conditions...');
      const res = await axios.get(`${API_BASE}/simulate_data`);
      setMapData(prev => ({...prev, hospitals: res.data.hospitals}));
      setStatusMsg('Traffic & Hospital load updated.');
      
      // Clear routes
      setGaResult(null);
      setBaselineResult(null);
    } catch (err) {
      console.error(err);
    }
  };

  const runRouting = async () => {
    if (!startNode) return;
    
    setLoading(true);
    setStatusMsg('Running Genetic Algorithm & Baseline Routing...');
    
    try {
      const payload = { start_node: startNode, urgency: parseInt(urgency) };
      
      // Run Baseline
      const baseRes = await axios.post(`${API_BASE}/baseline_route`, payload);
      
      // Run GA
      const gaRes = await axios.post(`${API_BASE}/run_ga`, payload);
      
      if (baseRes.data.error || gaRes.data.error) {
          setStatusMsg(baseRes.data.error || gaRes.data.error);
          setGaResult(null);
          setBaselineResult(null);
          setLoading(false);
          return;
      }
      
      setBaselineResult(baseRes.data);
      setGaResult(gaRes.data);
      
      setStatusMsg('Routing Complete.');
    } catch (err) {
      console.error(err);
      setStatusMsg('Error calculating routes.');
    } finally {
      setLoading(false);
    }
  };

  const handleMapClick = async (lat, lon) => {
    if (!mapData) return;
    try {
      setStatusMsg('Updating start location...');
      const res = await axios.get(`${API_BASE}/nearest_node?lat=${lat}&lon=${lon}`);
      if (res.data.status === 'success') {
        setStartNode(res.data.node);
        setStartNodeCoords(res.data.coords);
        setStatusMsg('Location updated. Ready to route.');
        // Clear previous routes
        setGaResult(null);
        setBaselineResult(null);
      }
    } catch (err) {
      console.error(err);
      setStatusMsg('Error updating location.');
    }
  };

  return (
    <div className="h-screen w-screen bg-background text-text-main flex flex-col p-4 md:p-6 gap-6 font-sans">
      {/* Header */}
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black bg-linear-to-r from-blue-400 via-indigo-400 to-emerald-400 bg-clip-text text-transparent tracking-tight">
            RISK SENTINEL: AMBULANCE
          </h1>
          <p className="text-text-muted mt-0.5 text-xs font-medium tracking-widest uppercase opacity-70">
            Hybrid Soft Computing Framework • GA + ANN + FUZZY
          </p>
        </div>
        
        <div className="glass px-4 py-2 rounded-2xl flex items-center space-x-3 border border-white/10 shadow-2xl">
          <div className="flex -space-x-2">
             <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></div>
             <div className={`w-2 h-2 rounded-full ${loading ? 'bg-warning' : 'bg-secondary'}`}></div>
          </div>
          <span className="text-[11px] font-bold uppercase tracking-widest text-text-muted">{statusMsg}</span>
        </div>
      </header>

      {/* Main Content Grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        
        {/* Left Panel - Controls & Dashboard */}
        <div className="lg:col-span-4 flex flex-col gap-6 overflow-hidden">
          
          {/* Controls Panel */}
          <div className="glass p-6 rounded-3xl shadow-2xl border border-white/5 flex flex-col gap-5 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 blur-3xl rounded-full -mr-16 -mt-16 group-hover:bg-primary/20 transition-colors"></div>
            
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">Control Center</h2>
              <button onClick={initSystem} className="text-xs text-primary hover:underline">Reset Map</button>
            </div>
            
            <div className="space-y-4">
               <div className="bg-white/5 p-4 rounded-2xl border border-white/5">
                  <div className="flex justify-between items-end mb-3">
                    <label className="text-xs font-bold uppercase tracking-wider text-text-muted">Emergency Urgency</label>
                    <span className={`text-2xl font-black ${urgency > 7 ? 'text-danger' : 'text-primary'}`}>{urgency}</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" max="10" 
                    value={urgency} 
                    onChange={(e) => setUrgency(e.target.value)}
                    className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                  <div className="flex justify-between text-[10px] font-bold text-text-muted mt-2 uppercase tracking-tighter">
                    <span>Routine</span>
                    <span className="text-danger/70">Critical</span>
                  </div>
               </div>

               <div className="flex flex-col gap-3">
                  <button 
                    onClick={runRouting}
                    disabled={loading || !mapData}
                    className="group relative w-full py-4 bg-primary hover:bg-primary-dark transition-all rounded-2xl font-bold text-sm shadow-[0_10px_30px_rgba(59,130,246,0.3)] disabled:opacity-50 overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                    <span className="relative flex items-center justify-center gap-2">
                       <Navigation2 size={16} /> FIND OPTIMAL ROUTE
                    </span>
                  </button>
                  
                  <button 
                    onClick={simulateTraffic}
                    disabled={loading || !mapData}
                    className="w-full py-3 bg-white/5 hover:bg-white/10 transition-all border border-white/10 rounded-2xl font-bold text-[10px] tracking-widest uppercase text-text-muted"
                  >
                    Update Real-Time Traffic
                  </button>
               </div>
            </div>
          </div>

          {/* Dashboard Panel */}
          <div className="glass p-6 rounded-2xl shadow-xl border border-surface flex-1 min-h-0 overflow-y-auto">
             <Dashboard gaResult={gaResult} baselineResult={baselineResult} />
          </div>

        </div>

        {/* Right Panel - Map */}
        <div className="lg:col-span-8 relative h-full min-h-[400px]">
          {mapData ? (
             <MapComponent 
                center={mapData.map_center ? [mapData.map_center.lat, mapData.map_center.lon] : [mapData.sample_coords.lat, mapData.sample_coords.lon]}
                startNodeCoords={startNodeCoords}
                hospitals={mapData.hospitals}
                gaRoute={gaResult ? gaResult.coords : null}
                baselineRoute={baselineResult ? baselineResult.coords : null}
                onMapClick={handleMapClick}
             />
          ) : (
            <div className="w-full h-full glass rounded-2xl flex items-center justify-center border border-surface">
              <div className="animate-pulse text-lg text-text-muted">Loading Map Data...</div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;
