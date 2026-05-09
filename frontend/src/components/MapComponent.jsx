import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, useMapEvents, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet's default icon path issues with Vite
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// Custom Icons
const hospitalIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const startIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Component to dynamically fit bounds when route changes
const ChangeView = ({ center, zoom, bounds }) => {
    const map = useMap();
    useEffect(() => {
        if (bounds && bounds.length > 0) {
            map.fitBounds(bounds, { padding: [50, 50] });
        } else if (center) {
            map.setView(center, zoom);
        }
    }, [center, zoom, bounds, map]);
    return null;
}

const MapEventsHandler = ({ onMapClick }) => {
    useMapEvents({
        click(e) {
            if (onMapClick) onMapClick(e.latlng.lat, e.latlng.lng);
        }
    });
    return null;
}

const MapComponent = ({ center, hospitals, startNodeCoords, gaRoute, baselineRoute, onMapClick }) => {
    
    // Compute bounds based on all routes to fit map nicely
    let bounds = [];
    if (gaRoute && gaRoute.length > 0) {
        bounds = [...bounds, ...gaRoute];
    }
    if (baselineRoute && baselineRoute.length > 0) {
        bounds = [...bounds, ...baselineRoute];
    }

    return (
        <div className="w-full h-full rounded-2xl overflow-hidden shadow-2xl border border-surface relative z-0">
            <MapContainer 
                center={center} 
                zoom={14} 
                className="w-full h-full"
                zoomControl={false}
            >
                {/* Dark theme map tiles */}
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />
                
                <ChangeView center={center} zoom={14} bounds={bounds.length > 0 ? bounds : null} />
                <MapEventsHandler onMapClick={onMapClick} />

                {/* 10km Playable Zone Radius */}
                <Circle 
                    center={center} 
                    radius={10000} 
                    pathOptions={{ 
                        color: '#3b82f6', 
                        fillColor: '#3b82f6', 
                        fillOpacity: 0.03, 
                        weight: 1, 
                        dashArray: '5, 10' 
                    }} 
                />

                {/* Start Marker */}
                {startNodeCoords && (
                    <Marker position={[startNodeCoords.lat, startNodeCoords.lon]} icon={startIcon}>
                        <Popup>Emergency Location</Popup>
                    </Marker>
                )}

                {/* Hospital Markers */}
                {hospitals.map((h, idx) => (
                    // We don't have exact lat/lon for hospitals here unless passed, 
                    // but we can assume they are handled or not displayed if coords missing.
                    // Actually, let's just let backend pass coords or rely on route ends.
                    h.coords ? (
                        <Marker key={idx} position={[h.coords.lat, h.coords.lon]} icon={hospitalIcon}>
                            <Popup>
                                <div className="font-bold text-lg">{h.name}</div>
                                <div className="text-sm">Load: {['Low', 'Medium', 'High'][h.capacity_load]}</div>
                            </Popup>
                        </Marker>
                    ) : null
                ))}

                {/* Baseline Route (Dijkstra) - Gray/White dashed */}
                {baselineRoute && baselineRoute.length > 0 && (
                    <Polyline 
                        positions={baselineRoute} 
                        pathOptions={{ color: '#94a3b8', weight: 4, dashArray: '10, 10', opacity: 0.7 }} 
                    />
                )}

                {/* GA Route - Vibrant Gradient/Blue */}
                {gaRoute && gaRoute.length > 0 && (
                    <Polyline 
                        positions={gaRoute} 
                        pathOptions={{ color: '#3b82f6', weight: 6, opacity: 0.9 }} 
                    />
                )}
            </MapContainer>
        </div>
    );
};

export default MapComponent;
