import React from 'react';
import { globalStore } from '../state';

export const Graph: React.FC = () => {
  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      <div className="rounded-3xl bg-white border border-slate-200 p-8 shadow-sm">
        <h1 className="text-3xl font-black text-[#0F172A]">Neo4j Cluster Entity Relationship Map</h1>
        <p className="text-slate-500 text-sm mt-1">Real-time graph tracing connecting clinical accounts, patient databases, and external subnets.</p>
      </div>

      <div className="rounded-3xl bg-white border border-slate-200 p-16 text-center space-y-6 shadow-sm relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(79,70,229,0.05),transparent_70%)]"></div>
        <div className="relative z-10 space-y-4">
          <div className="w-20 h-20 rounded-3xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-[#4F46E5] mx-auto shadow-inner animate-pulse">
            <span className="text-2xl font-black font-mono">NODE</span>
          </div>
          <h3 className="text-xl font-bold text-[#0F172A]">Forensic Knowledge Graph Active</h3>
          <p className="text-slate-500 text-sm max-w-md mx-auto font-medium">
            Mapping behavioral paths between Doctor #DR001 and unauthorized IP subnet 192.168.44.12.
          </p>
          <div className="pt-4">
            <button 
              onClick={() => globalStore.setState({ route: 'dashboard' })}
              className="px-6 py-2.5 rounded-xl bg-slate-900 text-white font-semibold text-xs hover:bg-slate-800 transition-colors"
            >
              ← Return to Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};