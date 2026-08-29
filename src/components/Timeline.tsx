import React, { useEffect, useState } from 'react';
import { globalStore, AppState, detailedTimelineEvents } from '../state';

export const Timeline: React.FC = () => {
  const [, setState] = useState<AppState>(globalStore.getState());

  useEffect(() => {
    return globalStore.subscribe(setState);
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto animate-fade-in">
      <div className="rounded-3xl bg-white border border-slate-200 p-8 shadow-sm">
        <div className="flex items-center space-x-3 mb-4">
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold font-mono">🟢 ACTIVE INVESTIGATION</span>
          <span className="px-3 py-1 rounded-full bg-rose-100 text-rose-600 text-xs font-bold font-mono">🚨 Critical Severity</span>
        </div>
        <h1 className="text-3xl font-black text-[#0F172A]">Case MT-2026-001: Unauthorized EHR Harvest</h1>
        <p className="text-slate-500 text-sm mt-1">Deep forensic reconstruction of session telemetry for User #DR001.</p>
      </div>

      <div className="rounded-3xl bg-white border border-slate-200 p-8 shadow-sm space-y-6">
        <h3 className="text-lg font-bold text-[#0F172A]">Interactive Forensic Timeline</h3>
        <div className="space-y-4">
          {detailedTimelineEvents.map((item, index) => (
            <div key={index} className="flex items-start space-x-4 p-4 rounded-2xl bg-[#F8FAFC] border border-slate-200">
              <div className="w-8 h-8 rounded-full bg-white border-2 border-slate-300 flex items-center justify-center font-bold text-xs text-[#4F46E5]">⚡</div>
              <div className="flex-1 flex justify-between items-center">
                <div>
                  <span className="text-[10px] font-mono text-slate-400 font-semibold">{item.time}</span>
                  <h4 className="text-xs font-bold text-[#0F172A]">{item.event}</h4>
                  <p className="text-xs text-slate-500 mt-0.5">{item.action} ({item.device})</p>
                </div>
                <span className="text-xs font-mono bg-indigo-50 text-[#4F46E5] px-2.5 py-1 rounded-full font-semibold">{item.type}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="pt-4">
          <button 
            onClick={() => globalStore.setState({ route: 'dashboard' })}
            className="px-6 py-2.5 rounded-xl bg-slate-900 text-white font-semibold text-xs hover:bg-slate-800 transition-colors"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};