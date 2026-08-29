import React, { useEffect, useState } from 'react';
import { globalStore, AppState } from '../state';

export const Alerts: React.FC = () => {
  const [state, setState] = useState<AppState>(globalStore.getState());

  useEffect(() => {
    return globalStore.subscribe(setState);
  }, []);

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      <div className="rounded-3xl bg-white border border-slate-200 p-8 shadow-sm">
        <h1 className="text-3xl font-black text-[#0F172A]">Security Alerts & Telemetry</h1>
        <p className="text-slate-500 text-sm mt-1">Real-time isolation feed and risk scoring matrix for hospital nodes.</p>
      </div>

      <div className="rounded-3xl bg-white border border-slate-200 p-6 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400 uppercase">
                <th className="pb-3">Scenario / Title</th>
                <th className="pb-3">User ID</th>
                <th className="pb-3">Role</th>
                <th className="pb-3">Risk Score</th>
                <th className="pb-3">Location</th>
                <th className="pb-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {state.notificationHistory.map((item, index) => (
                <tr key={index} className="hover:bg-slate-50">
                  <td className="py-4 font-bold text-[#0F172A]">{item.title}</td>
                  <td className="py-4 text-[#4F46E5] font-bold font-mono">{item.user}</td>
                  <td className="py-4 text-slate-600">{item.role}</td>
                  <td className="py-4 text-rose-600 font-bold font-mono">{item.risk}%</td>
                  <td className="py-4 text-slate-600">{item.location}</td>
                  <td className="py-4">
                    <button 
                      onClick={() => globalStore.setState({ route: 'timeline-page' })}
                      className="px-3 py-1 rounded-xl bg-indigo-50 text-[#4F46E5] text-xs font-bold hover:bg-indigo-100 transition-colors"
                    >
                      Inspect Timeline →
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