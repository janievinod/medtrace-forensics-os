import React, { useEffect, useState } from 'react';
import { globalStore, AppState } from '../state';

export const Dashboard: React.FC = () => {
  const [state, setState] = useState<AppState>(globalStore.getState());

  useEffect(() => {
    return globalStore.subscribe(setState);
  }, []);

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-black text-[#0F172A]">Executive Security Overview</h1>
        <p className="text-sm text-slate-600">Real-time threat telemetry, EHR anomaly detection, and automated audit trails.</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="rounded-3xl bg-white border border-slate-200 p-6 shadow-sm">
          <span className="text-xs font-semibold uppercase text-slate-500">🚨 Critical Alerts</span>
          <div className="text-3xl font-black text-[#0F172A] mt-1">{state.notificationHistory.length}</div>
        </div>
        <div className="rounded-3xl bg-white border border-slate-200 p-6 shadow-sm">
          <span className="text-xs font-semibold uppercase text-slate-500">⚠ High Risk Users</span>
          <div className="text-3xl font-black text-[#0F172A] mt-1">7</div>
        </div>
        <div className="rounded-3xl bg-white border border-slate-200 p-6 shadow-sm">
          <span className="text-xs font-semibold uppercase text-slate-500">📁 Investigations</span>
          <div className="text-3xl font-black text-[#0F172A] mt-1">104</div>
        </div>
        <div className="rounded-3xl bg-white border border-slate-200 p-6 shadow-sm">
          <span className="text-xs font-semibold uppercase text-slate-500">🎯 Accuracy</span>
          <div className="text-3xl font-black text-emerald-600 mt-1">94%</div>
        </div>
      </div>

      {/* Recent Alerts Table Preview */}
      <div className="rounded-3xl bg-white border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-bold text-[#0F172A] mb-4">Active Telemetry Feed</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400 uppercase">
                <th className="pb-3">Title / Scenario</th>
                <th className="pb-3">User ID</th>
                <th className="pb-3">Risk Score</th>
                <th className="pb-3">Location</th>
                <th className="pb-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {state.notificationHistory.map((item, index) => (
                <tr key={index} className="hover:bg-slate-50">
                  <td className="py-4 font-bold text-[#0F172A]">{item.title}</td>
                  <td className="py-4 text-[#4F46E5] font-bold">{item.user}</td>
                  <td className="py-4 text-rose-600 font-bold">{item.risk}</td>
                  <td className="py-4 text-slate-600">{item.location}</td>
                  <td className="py-4">
                    <button 
                      onClick={() => globalStore.setState({ route: 'timeline-page' })}
                      className="px-3 py-1 rounded-xl bg-indigo-50 text-[#4F46E5] text-xs font-bold hover:bg-indigo-100 transition-colors"
                    >
                      Timeline →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};