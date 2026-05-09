import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Clock, Map, Navigation2 } from 'lucide-react';

const StatCard = ({ icon: Icon, title, value, unit, color, trend }) => (
    <div className="glass p-4 rounded-xl flex items-center justify-between border border-white/5 hover:border-white/10 transition-all">
        <div className="flex items-center space-x-4">
            <div className={`p-3 rounded-xl bg-${color}-500/20 text-${color}-400`}>
                <Icon size={20} />
            </div>
            <div>
                <p className="text-xs text-text-muted font-medium uppercase tracking-wider">{title}</p>
                <p className="text-xl font-bold">
                    {value} <span className="text-xs font-normal text-text-muted">{unit}</span>
                </p>
            </div>
        </div>
        {trend !== undefined && trend !== null && (
            <div className={`text-xs font-bold px-2 py-1 rounded-full ${trend <= 0 ? 'bg-success-500/20 text-success-400' : 'bg-danger-500/20 text-danger-400'}`}>
                {trend <= 0 ? '↓' : '↑'} {Math.abs(trend)}%
            </div>
        )}
    </div>
);

const ComparisonBar = ({ label, gaVal, baseVal, unit = "min", type = "time", reverse = false }) => {
    const maxVal = Math.max(gaVal, baseVal, 0.1);
    const gaWidth = (gaVal / maxVal) * 100;
    const baseWidth = (baseVal / maxVal) * 100;
    
    // For time/delay, smaller is better (primary color). For survival, larger is better.
    const gaColor = reverse ? (gaVal > baseVal ? 'text-success-400' : 'text-danger-400') : (gaVal < baseVal ? 'text-primary' : 'text-danger-400');
    
    return (
        <div className="space-y-1">
            <div className="flex justify-between text-[10px] uppercase tracking-wider font-bold">
                <span className="text-text-muted">{label}</span>
                <span>
                    <span className={gaColor}>GA: {gaVal.toFixed(1)}{unit}</span>
                    <span className="mx-2 text-white/20">|</span>
                    <span className="text-text-muted">A*: {baseVal.toFixed(1)}{unit}</span>
                </span>
            </div>
            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden flex flex-col gap-0.5">
                <div className={`h-full ${reverse ? (gaVal > baseVal ? 'bg-success-500' : 'bg-danger-500') : (gaVal < baseVal ? 'bg-primary' : 'bg-danger-500')} rounded-full`} style={{ width: `${gaWidth}%` }}></div>
                <div className="h-full bg-white/20 rounded-full" style={{ width: `${baseWidth}%` }}></div>
            </div>
        </div>
    );
};

const Dashboard = ({ gaResult, baselineResult }) => {
    
    // Prepare chart data
    let chartData = [];
    if (gaResult && gaResult.convergence) {
        chartData = gaResult.convergence.map((cost, idx) => ({
            generation: idx + 1,
            cost: Math.round(cost)
        }));
    }

    const calcImprovement = (gaVal, baseVal) => {
        if (!gaVal || !baseVal) return null;
        const diff = ((gaVal - baseVal) / baseVal) * 100;
        return Math.round(diff);
    };

    return (
        <div className="flex flex-col space-y-6 h-full text-text-main overflow-y-auto pr-2 custom-scrollbar">
            
            {/* Scenario Insights */}
            <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-white/10 pb-2">
                    <h2 className="text-lg font-bold flex items-center gap-2">
                        <Activity size={18} className="text-secondary" />
                        AI Intelligence Insights
                    </h2>
                    <span className="text-[10px] bg-secondary/20 text-secondary px-2 py-0.5 rounded-full font-bold uppercase tracking-tighter">Live</span>
                </div>
                {gaResult && baselineResult ? (
                    <div className="space-y-4 bg-white/5 p-4 rounded-xl border border-white/5">
                        <div className="grid grid-cols-2 gap-3 mb-2">
                             <div className="glass p-3 rounded-xl border border-primary/20 bg-primary/5">
                                <p className="text-[10px] text-primary uppercase font-bold">Survival Probability</p>
                                <p className="text-2xl font-black text-success-400">{gaResult.breakdown?.survival_probability.toFixed(0)}%</p>
                                <p className="text-[9px] text-text-muted italic">Condition: {gaResult.breakdown?.patient_condition}</p>
                             </div>
                             <div className="glass p-3 rounded-xl border border-white/10">
                                <p className="text-[10px] text-text-muted uppercase font-bold">A* Baseline</p>
                                <p className="text-2xl font-black text-white/30">{baselineResult.breakdown?.survival_probability.toFixed(0)}%</p>
                                <p className="text-[9px] text-text-muted italic">Loss: {(baselineResult.breakdown?.survival_probability - gaResult.breakdown?.survival_probability).toFixed(1)}%</p>
                             </div>
                        </div>

                        <div className="grid grid-cols-1 gap-4">
                            <ComparisonBar 
                                label="Physical Distance" 
                                gaVal={gaResult.distance / 1000} 
                                baseVal={baselineResult.distance / 1000}
                                unit="km"
                            />
                            <ComparisonBar 
                                label="Avg Velocity (Traffic Adjusted)" 
                                gaVal={gaResult.breakdown?.avg_speed_kph || 0} 
                                baseVal={baselineResult.breakdown?.avg_speed_kph || 0}
                                unit="km/h"
                                reverse={true}
                            />
                            <ComparisonBar 
                                label="Traffic & Accident Delay" 
                                gaVal={gaResult.breakdown?.traffic_delay_min || 0} 
                                baseVal={baselineResult.breakdown?.traffic_delay_min || 0}
                            />
                            <ComparisonBar 
                                label="Hospital Admission Lag" 
                                gaVal={gaResult.breakdown?.hospital_penalty_min || 0} 
                                baseVal={baselineResult.breakdown?.hospital_penalty_min || 0}
                            />
                        </div>
                        
                        <div className="pt-3 border-t border-white/10 flex items-center justify-between">
                            <div>
                                <p className="text-[10px] text-secondary font-bold uppercase mb-1">Incident Report:</p>
                                <div className="flex gap-3 text-[10px]">
                                    <span className="text-text-muted">GA Avoided: <span className="text-white font-bold">{baselineResult.breakdown?.blocked_incidents - gaResult.breakdown?.blocked_incidents}</span> Blocks</span>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="text-[10px] text-primary font-bold uppercase">Total Lead Time</p>
                                <p className="text-xs font-bold text-success-400">-{ (baselineResult.breakdown?.total_effective_time - gaResult.breakdown?.total_effective_time).toFixed(1) } min</p>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="text-xs italic text-text-muted py-2">Analyzing road network metadata... Click "Find Optimal Route" to trigger AI decision logic.</div>
                )}
            </div>

            <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-white/10 pb-2">
                    <h2 className="text-lg font-bold flex items-center gap-2">
                        <Navigation2 size={18} className="text-primary" />
                        GA Optimized Route
                    </h2>
                    <div className="flex gap-2">
                        <div className="w-3 h-3 bg-primary rounded-full shadow-[0_0_8px_#3b82f6]"></div>
                    </div>
                </div>
                
                {gaResult ? (
                    <div className="grid grid-cols-1 gap-3">
                        <StatCard 
                            icon={Clock} 
                            title="Travel Time" 
                            value={(gaResult.time_seconds / 60).toFixed(1)} 
                            unit="min" 
                            color="primary" 
                            trend={calcImprovement(gaResult.time_seconds, baselineResult?.time_seconds)}
                        />
                        <StatCard 
                            icon={Activity} 
                            title="Congestion Score" 
                            value={gaResult.congestion_score.toFixed(1)} 
                            unit="/ 10" 
                            color="danger" 
                            trend={calcImprovement(gaResult.congestion_score, baselineResult?.congestion_score)}
                        />
                        <div className="grid grid-cols-2 gap-3">
                            <div className="glass p-3 rounded-xl border border-white/5">
                                <p className="text-[10px] text-text-muted uppercase">Hospital</p>
                                <p className="text-sm font-bold truncate">{gaResult.hospital?.name}</p>
                            </div>
                            <div className="glass p-3 rounded-xl border border-white/5">
                                <p className="text-[10px] text-text-muted uppercase">Distance</p>
                                <p className="text-sm font-bold">{(gaResult.distance / 1000).toFixed(2)} km</p>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="h-24 flex items-center justify-center border-2 border-dashed border-white/5 rounded-xl text-text-muted text-sm italic">
                        No route calculated yet
                    </div>
                )}
            </div>

            {/* Final Medical Outcome Analysis */}
            {gaResult && baselineResult && (
                <div className="pt-4 border-t border-white/10">
                    <h3 className="text-xs font-bold uppercase tracking-widest text-secondary mb-3 italic">Final Medical Outcome Analysis</h3>
                    <div className="space-y-2">
                        <div className="flex justify-between items-center glass p-3 rounded-xl border border-success-500/20">
                            <span className="text-[11px] font-bold uppercase tracking-tighter">Treatment Ready (GA):</span>
                            <span className="text-lg font-black text-success-400">{gaResult.breakdown?.total_effective_time.toFixed(1)} min</span>
                        </div>
                        <div className="flex justify-between items-center glass p-3 rounded-xl border border-white/5 opacity-60">
                            <span className="text-[11px] uppercase tracking-tighter">Treatment Ready (A*):</span>
                            <span className="text-lg font-bold">{baselineResult.breakdown?.total_effective_time.toFixed(1)} min</span>
                        </div>
                        <p className="text-[10px] text-text-muted text-center pt-2 font-medium">
                            The Hybrid GA model saved <span className="text-success-400 font-bold">{(baselineResult.breakdown?.total_effective_time - gaResult.breakdown?.total_effective_time).toFixed(1)} minutes</span>, increasing survival by <span className="text-success-400">{(gaResult.breakdown?.survival_probability - baselineResult.breakdown?.survival_probability).toFixed(0)}%</span>.
                        </p>
                    </div>
                </div>
            )}

            {/* Genetic Convergence Chart */}
            {chartData.length > 0 && (
                <div className="mt-4 pt-4 border-t border-white/10">
                    <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                         Genetic Convergence Curve
                    </h2>
                    <div className="h-40 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <defs>
                                    <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.2}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                <XAxis dataKey="generation" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} hide />
                                <Tooltip 
                                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '12px' }}
                                    itemStyle={{ color: '#3b82f6' }}
                                    cursor={{ stroke: '#3b82f633', strokeWidth: 2 }}
                                />
                                <Line 
                                    type="monotone" 
                                    dataKey="cost" 
                                    stroke="#3b82f6" 
                                    strokeWidth={3}
                                    dot={{ r: 2, fill: '#3b82f6', strokeWidth: 0 }}
                                    activeDot={{ r: 4, fill: '#3b82f6', stroke: '#fff' }}
                                    animationDuration={1500}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}


            {/* Technical Source Info */}
            <div className="mt-auto pt-6">
                <div className="bg-primary/10 p-4 rounded-2xl border border-primary/20">
                    <h3 className="text-xs font-bold text-primary uppercase mb-2">Data Intelligence Source</h3>
                    <div className="grid grid-cols-2 gap-2 text-[10px]">
                        <div>
                            <p className="text-text-muted">Road Metadata:</p>
                            <p className="font-bold">OSM + RealSpeed</p>
                        </div>
                        <div>
                            <p className="text-text-muted">Traffic Logic:</p>
                            <p className="font-bold">ANN Prediction</p>
                        </div>
                        <div>
                            <p className="text-text-muted">Decision Engine:</p>
                            <p className="font-bold">Fuzzy Logic</p>
                        </div>
                        <div>
                            <p className="text-text-muted">Beds/Capacity:</p>
                            <p className="font-bold">Live Hybrid Sim</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
