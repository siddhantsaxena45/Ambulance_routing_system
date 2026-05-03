import React, { useState, useEffect } from 'react';
import axios from 'axios';
import MapComponent from './components/MapComponent';
import Dashboard from './components/Dashboard';

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
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-primary to-secondary bg-clip-text text-transparent">
            Intelligent Ambulance Routing
          </h1>
          <p className="text-text-muted mt-1 text-sm">
            Hybrid Soft Computing Framework using GA, ANN, and Fuzzy Logic
          </p>
        </div>
        
        <div className="glass px-4 py-2 rounded-lg flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${loading ? 'bg-warning animate-pulse' : 'bg-secondary'}`}></div>
          <span className="text-sm font-medium">{statusMsg}</span>
        </div>
      </header>

      {/* Main Content Grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        
        {/* Left Panel - Controls & Dashboard */}
        <div className="lg:col-span-4 flex flex-col gap-6 overflow-hidden">
          
          {/* Controls Panel */}
          <div className="glass p-6 rounded-2xl shadow-xl border border-surface flex flex-col gap-4">
            <h2 className="text-xl font-semibold mb-2">Control Panel</h2>
            
            <div>
              <label className="block text-sm text-text-muted mb-1">Emergency Urgency (0-10)</label>
              <input 
                type="range" 
                min="0" max="10" 
                value={urgency} 
                onChange={(e) => setUrgency(e.target.value)}
                className="w-full accent-primary"
              />
              <div className="flex justify-between text-xs text-text-muted mt-1">
                <span>Normal (0)</span>
                <span className="font-bold text-white text-base">{urgency}</span>
                <span className="text-danger">Critical (10)</span>
              </div>
            </div>

            <div className="pt-4 flex flex-col gap-3">
              <button 
                onClick={runRouting}
                disabled={loading || !mapData}
                className="w-full py-3 bg-primary hover:bg-primary-dark transition-colors rounded-xl font-semibold shadow-[0_0_15px_rgba(59,130,246,0.3)] disabled:opacity-50"
              >
                Find Optimal Route
              </button>
              
              <button 
                onClick={simulateTraffic}
                disabled={loading || !mapData}
                className="w-full py-3 bg-surface hover:bg-surface/80 transition-colors border border-gray-700 rounded-xl font-medium"
              >
                Simulate New Traffic
              </button>
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
