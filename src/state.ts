export type AppRoute = 
  | 'splash' 
  | 'login' 
  | 'landing' 
  | 'dashboard' 
  | 'alerts' 
  | 'timeline-page' 
  | 'graph' 
  | 'reports' 
  | 'settings' 
  | 'unauthorized-warning';

export interface AlertScenario {
  id: string;
  title: string;
  user: string;
  role: string;
  risk: number;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  location: string;
  description: string;
}

export interface TimelineEvent {
  time: string;
  event: string;
  type: string;
  ip: string;
  device: string;
  action: string;
  records: string;
}

export interface AppState {
  route: AppRoute;
  currentUser: { email: string; role: string } | null;
  selectedAlertId: string;
  demoMode: boolean;
  scenarioIndex: number;
  showPopup: boolean;
  bellShake: boolean;
  searchQuery: string;
  warningDetails: { user: string; time: string } | null;
  notificationHistory: AlertScenario[];
  activePopup: AlertScenario | null;
}

export const initialSimulationScenarios: AlertScenario[] = [
  { id: 'DR001', title: '🚨 Critical Alert', user: 'DR001', role: 'Doctor', risk: 92, severity: 'Critical', location: 'Chennai', description: 'Accessed 400 patient records at 2:00 AM and initiated bulk export.' },
  { id: 'NR021', title: '⚠ Insider Threat Detected', user: 'NR021', role: 'Nurse', risk: 84, severity: 'High', location: 'Coimbatore', description: 'Accessed records outside assigned department.' },
  { id: 'AD014', title: '🔒 Record Tampering Suspected', user: 'AD014', role: 'Administrator', risk: 89, severity: 'High', location: 'Bangalore', description: 'Multiple modifications detected in patient treatment records.' },
  { id: 'DR077', title: '📤 Possible Data Exfiltration', user: 'DR077', role: 'Doctor', risk: 95, severity: 'Critical', location: 'Hyderabad', description: 'Large volume download of medical records detected.' },
  { id: 'DR118', title: '🔑 Compromised Account Activity', user: 'DR118', role: 'Doctor', risk: 87, severity: 'High', location: 'Mumbai', description: 'Login from unknown device and unusual geographic location.' }
];

export const detailedTimelineEvents: TimelineEvent[] = [
  { time: '02:00 AM', event: 'User Login Detected', type: 'Authentication', ip: '192.168.44.12', device: 'NODE-CLINIC-884', action: 'Successful SSO Login', records: '0' },
  { time: '02:03 AM', event: 'New Device Identified', type: 'Security', ip: '192.168.44.12', device: 'Windows 11 Chrome', action: 'Unrecognized Subnet Handshake', records: '0' },
  { time: '02:05 AM', event: 'Accessed 120 Patient Records', type: 'EHR Access', ip: '192.168.44.12', device: 'NODE-CLINIC-884', action: 'Query Cardiology DB', records: '120' },
  { time: '02:10 AM', event: 'Accessed Additional Records', type: 'EHR Access', ip: '192.168.44.12', device: 'NODE-CLINIC-884', action: 'Query ICU DB', records: '280' },
  { time: '02:15 AM', event: 'Bulk Export Initiated', type: 'Exfiltration', ip: '192.168.44.12', device: 'NODE-CLINIC-884', action: 'API Payload Download (142MB)', records: '400' },
  { time: '02:18 AM', event: 'Integrity Verification Triggered', type: 'Ledger', ip: 'Internal', device: 'Smart Contract Ledger', action: 'Cryptographic Hash Check', records: '400' },
  { time: '02:20 AM', event: 'Critical Alert Generated', type: 'AI Engine', ip: 'Internal', device: 'Isolation Forest v2.4', action: 'Quarantine Protocol Dispatched', records: '400' },
  { time: '02:25 AM', event: 'Investigation Started', type: 'SOC Workflow', ip: 'Internal', device: 'MEDTRACE Forensic OS', action: 'Analyst Case File Created', records: '400' },
];

export class AppStateManager {
  private state: AppState;
  private listeners: ((state: AppState) => void)[] = [];

  constructor() {
    this.state = {
      route: 'splash',
      currentUser: null,
      selectedAlertId: 'DR001',
      demoMode: true,
      scenarioIndex: 0,
      showPopup: true,
      bellShake: false,
      searchQuery: '',
      warningDetails: null,
      notificationHistory: [initialSimulationScenarios[0]],
      activePopup: initialSimulationScenarios[0]
    };
  }

  public getState(): AppState {
    return this.state;
  }

  public setState(partial: Partial<AppState>) {
    this.state = { ...this.state, ...partial };
    this.listeners.forEach(listener => listener(this.state));
  }

  public subscribe(listener: (state: AppState) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }
}

export const globalStore = new AppStateManager();