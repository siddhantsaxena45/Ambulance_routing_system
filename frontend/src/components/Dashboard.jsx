import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Clock, Map, Navigation2 } from 'lucide-react';

const StatCard = ({ icon: Icon, title, value, unit, color }) => (
    <div className="glass p-4 rounded-xl flex items-center space-x-4">
        <div className={`p-3 rounded-full bg-${color}-500/20 text-${color}-400`}>
            <Icon size={24} />
        </div>
        <div>
            <p className="text-sm text-text-muted">{title}</p>
            <p className="text-xl font-bold">
                {value} <span className="text-sm font-normal text-text-muted">{unit}</span>
            </p>
        </div>
    </div>
);

const Dashboard = ({ gaResult, baselineResult }) => {
    
    // Prepare chart data
    let chartData = [];
    if (gaResult && gaResult.convergence) {
        chartData = gaResult.convergence.map((cost, idx) => ({
            generation: idx + 1,
            cost: Math.round(cost)
        }));
    }

    return (
        <div className="flex flex-col space-y-6 h-full text-text-main overflow-y-auto pr-2">
            
            <div className="space-y-4">
                <h2 className="text-xl font-semibold border-b border-surface pb-2">GA Optimized Route</h2>
                {gaResult ? (
                    <div className="grid grid-cols-2 gap-4">
                        <StatCard 
                            icon={Clock} 
                            title="Est. Time" 
                            value={(gaResult.time_seconds / 60).toFixed(1)} 
                            unit="min" 
                            color="primary" 
                        />
                        <StatCard 
                            icon={Activity} 
                            title="Congestion" 
                            value={gaResult.congestion_score.toFixed(1)} 
                            unit="/ 10" 
                            color="danger" 
                        />
                        <StatCard 
                            icon={Map} 
                            title="Target Hospital" 
                            value={gaResult.hospital?.name} 
                            unit="" 
                            color="secondary" 
                        />
                        <StatCard 
                            icon={Navigation2} 
                            title="Distance" 
                            value={(gaResult.distance / 1000).toFixed(2)} 
                            unit="km" 
                            color="success" 
                        />
                        <StatCard 
                            icon={Navigation2} 
                            title="Cost Metric" 
                            value={Math.round(gaResult.cost)} 
                            unit="" 
                            color="warning" 
                        />
                    </div>
                ) : (
                    <p className="text-text-muted text-sm italic">Run GA to view metrics.</p>
                )}
            </div>

            <div className="space-y-4">
                <h2 className="text-xl font-semibold border-b border-surface pb-2">Baseline (Dijkstra)</h2>
                {baselineResult ? (
                    <div className="grid grid-cols-2 gap-4 opacity-80">
                        <StatCard 
                            icon={Clock} 
                            title="Est. Time" 
                            value={(baselineResult.time_seconds / 60).toFixed(1)} 
                            unit="min" 
                            color="text-muted" 
                        />
                        <StatCard 
                            icon={Activity} 
                            title="Congestion" 
                            value={baselineResult.congestion_score.toFixed(1)} 
                            unit="/ 10" 
                            color="text-muted" 
                        />
                        <StatCard 
                            icon={Navigation2} 
                            title="Distance" 
                            value={(baselineResult.distance / 1000).toFixed(2)} 
                            unit="km" 
                            color="text-muted" 
                        />
                        <StatCard 
                            icon={Map} 
                            title="Target Hospital" 
                            value={baselineResult.hospital?.name.substring(0, 20)} 
                            unit="" 
                            color="text-muted" 
                        />
                    </div>
                ) : (
                    <p className="text-text-muted text-sm italic">Run Baseline to view metrics.</p>
                )}
            </div>

            {chartData.length > 0 && (
                <div className="mt-4 pt-4 border-t border-surface grow">
                    <h2 className="text-xl font-semibold mb-4">GA Convergence</h2>
                    <div className="h-48 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                <XAxis dataKey="generation" stroke="#94a3b8" fontSize={12} tickLine={false} />
                                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} />
                                <Tooltip 
                                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
                                    itemStyle={{ color: '#3b82f6' }}
                                />
                                <Line 
                                    type="monotone" 
                                    dataKey="cost" 
                                    stroke="#3b82f6" 
                                    strokeWidth={3}
                                    dot={false}
                                    animationDuration={1500}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
