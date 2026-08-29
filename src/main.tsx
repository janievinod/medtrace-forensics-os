import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';

const Root: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] flex items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-2xl font-black">MEDTRACE Forensic OS Active</h1>
        <p className="text-sm text-slate-600 font-medium">Vite + React + TypeScript Stack Initialized.</p>
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);