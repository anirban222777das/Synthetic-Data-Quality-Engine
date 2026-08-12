import React, { useState, useRef, useEffect, Component } from 'react';
import { 
  Upload, 
  FileText, 
  Download, 
  AlertTriangle, 
  Activity, 
  BarChart, 
  Search,
  Shield,
  ShieldAlert,
  GitMerge,
  Cpu,
  Check,
  Database,
  Settings,
  ChevronDown,
  ChevronUp,
  Wand2
} from 'lucide-react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ color: 'red', padding: '2rem' }}>
          <h2>UI Render Error:</h2>
          <pre>{this.state.error.toString()}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

const PIPELINE_STEPS = [
  { id: 'analyze', label: 'Analyze Schema', icon: Search },
  { id: 'privacy', label: 'Privacy Scan', icon: Shield },
  { id: 'copula', label: 'Multivariate Copulas', icon: GitMerge },
  { id: 'generate', label: 'Synthesize Data', icon: Cpu },
  { id: 'validate', label: 'Validate Fidelity', icon: Check }
];

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [report, setReport] = useState(null);
  const [syntheticCsv, setSyntheticCsv] = useState(null);
  const [error, setError] = useState("");
  const [epsilon, setEpsilon] = useState("");
  const [conditionalBy, setConditionalBy] = useState("");
  const [smartPii, setSmartPii] = useState(false);
  const [autoClean, setAutoClean] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  
  const [scoreProgress, setScoreProgress] = useState(0);

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (report && !loading) {
      setTimeout(() => setScoreProgress(report.quality_score), 100);
    } else {
      setScoreProgress(0);
    }
  }, [report, loading]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError("");
      setReport(null);
    }
  };

  const handleGenerate = async () => {
    if (!file) return;
    setLoading(true);
    setLoadingStep(0);
    setError("");
    
    const startTime = Date.now();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('rows', 1000); 
    formData.append('seed', 42);
    if (epsilon) formData.append('epsilon', parseFloat(epsilon));
    if (conditionalBy) formData.append('conditional_by', conditionalBy);
    if (smartPii) formData.append('smart_pii', true);
    if (autoClean) formData.append('auto_clean', true);

    try {
      const response = await fetch('http://localhost:8000/api/generate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Generation failed");
      }

      const data = await response.json();
      
      const elapsed = Date.now() - startTime;
      const requiredTime = (PIPELINE_STEPS.length - 1) * 1200; // slightly faster animation
      const remainingDelay = Math.max(0, requiredTime - elapsed);
      
      // We simulate step progress
      const interval = setInterval(() => {
          setLoadingStep(prev => {
              if (prev < PIPELINE_STEPS.length - 1) return prev + 1;
              clearInterval(interval);
              return prev;
          });
      }, 1200);

      setTimeout(() => {
          clearInterval(interval);
          setLoadingStep(PIPELINE_STEPS.length - 1);
          setTimeout(() => {
              setReport(data.report);
              setSyntheticCsv(data.synthetic_csv);
              setLoading(false);
          }, 800);
      }, remainingDelay);

    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const downloadCsv = () => {
    if (!syntheticCsv) return;
    const blob = new Blob([syntheticCsv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'synthetic_data.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadJson = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'synthetic_quality_report.json');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatNum = (val, decimals = 2) => {
    if (typeof val === 'number' && !isNaN(val)) return val.toFixed(decimals);
    return 'N/A';
  };

  const renderErrorBar = (errorValue) => {
    if (typeof errorValue !== 'number' || isNaN(errorValue)) {
      return <span style={{ color: 'var(--text-muted)' }}>N/A</span>;
    }
    const widthPct = Math.min(Math.abs(errorValue) * 100, 100);
    const isGood = widthPct < 5;
    const isOk = widthPct < 20;
    const barColor = isGood ? 'var(--success)' : isOk ? 'var(--warning)' : 'var(--danger)';
    
    return (
      <div>
        <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-main)' }}>{formatNum(errorValue, 4)}</span>
        <div className="error-bar-container">
          <div className="error-bar-fill" style={{ width: `${widthPct}%`, background: barColor }}></div>
        </div>
      </div>
    );
  };

  return (
    <div className="app-container">
      <header>
        <h1>Synthetic Data Engine</h1>
        <p className="subtitle">High-fidelity deterministic generation via classical statistics.</p>
      </header>

      {!report && !loading && (
        <main>
          <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <div 
              className="upload-zone"
              onClick={() => fileInputRef.current.click()}
            >
              <Upload size={32} className="upload-icon" />
              {file ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <FileText size={16} style={{ color: 'var(--text-main)' }} />
                  <span style={{ fontSize: '1rem', fontWeight: 500 }}>{file.name}</span>
                </div>
              ) : (
                <>
                  <h3 style={{ marginBottom: '0.25rem', paddingBottom: 0, borderBottom: 'none', justifyContent: 'center' }}>Upload Reference Dataset</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>CSV format. All processing is strictly local.</p>
                </>
              )}
              <input 
                type="file" 
                accept=".csv" 
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
            </div>

            {error && <div style={{ color: 'var(--danger)', marginTop: '1rem', fontSize: '0.9rem' }}>{error}</div>}

            {file && (
              <div style={{ marginTop: '2rem', textAlign: 'left' }}>
                <div 
                  className="config-accordion-header" 
                  onClick={() => setShowConfig(!showConfig)}
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 500 }}>
                    <Settings size={18} /> Advanced Configuration
                  </div>
                  {showConfig ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>

                {showConfig && (
                  <div style={{ padding: '1.5rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', borderTop: 'none', borderRadius: '0 0 8px 8px', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <div>
                          <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-main)' }}><Wand2 size={14} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '4px' }} /> Smart PII Faker</label>
                          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>Use Faker to generate 100% synthetic, clean names and emails instead of shuffling them.</p>
                       </div>
                       <label className="toggle-switch">
                          <input type="checkbox" checked={smartPii} onChange={(e) => setSmartPii(e.target.checked)} />
                          <span className="slider"></span>
                       </label>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <div>
                          <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-main)' }}><Activity size={14} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '4px' }} /> Auto-Clean Outliers (IQR)</label>
                          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>Automatically cap extreme numeric outliers in the synthetic data using IQR boundaries.</p>
                       </div>
                       <label className="toggle-switch">
                          <input type="checkbox" checked={autoClean} onChange={(e) => setAutoClean(e.target.checked)} />
                          <span className="slider"></span>
                       </label>
                    </div>

                    <hr style={{ borderColor: 'var(--border)', margin: '0.5rem 0' }} />

                    <div>
                       <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 500, marginBottom: '0.5rem', color: 'var(--text-main)' }}><Shield size={14} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '4px' }} /> Differential Privacy Budget (ε)</label>
                       <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Lower values increase privacy via Laplace noise. Leave empty for max accuracy.</p>
                       <input type="number" step="0.1" min="0.1" max="10.0" value={epsilon} onChange={(e) => setEpsilon(e.target.value)} placeholder="e.g. 1.0 (Optional)" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border)', color: 'var(--text-main)', outline: 'none' }} />
                    </div>
                    
                    <div>
                       <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 500, marginBottom: '0.5rem', color: 'var(--text-main)' }}><GitMerge size={14} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '4px' }} /> Conditional Group-By Column</label>
                       <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Type the exact name of a categorical column to synthesize subgroups independently.</p>
                       <input type="text" value={conditionalBy} onChange={(e) => setConditionalBy(e.target.value)} placeholder="e.g. department (Optional)" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border)', color: 'var(--text-main)', outline: 'none' }} />
                    </div>
                  </div>
                )}
              </div>
            )}

            <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                className="btn" 
                onClick={handleGenerate} 
                disabled={!file}
              >
                Synthesize <Activity size={16} />
              </button>
            </div>
          </div>
        </main>
      )}

      {loading && (
        <main>
          <div className="glass-panel" style={{ maxWidth: '800px', margin: '0 auto', padding: '3rem 2rem' }}>
            <h3 style={{ borderBottom: 'none', justifyContent: 'center', marginBottom: '3rem', color: 'var(--text-main)' }}>Processing Pipeline Active</h3>
            
            <div className="pipeline-container">
              <div className="pipeline-track">
                 <div 
                    className="pipeline-progress" 
                    style={{ width: `${(loadingStep / (PIPELINE_STEPS.length - 1)) * 100}%` }}
                 ></div>
              </div>

              {PIPELINE_STEPS.map((step, idx) => {
                const isCompleted = idx < loadingStep;
                const isActive = idx === loadingStep;
                const Icon = step.icon;
                
                return (
                  <div key={idx} className={`pipeline-node-wrapper ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
                    <div className={`pipeline-node ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}>
                      <Icon size={16} />
                    </div>
                    <span className="pipeline-label">{step.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </main>
      )}

      {report && !loading && (
        <ErrorBoundary>
        <main style={{ animation: 'fadeIn 0.5s ease' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
            <h2>Generation Report</h2>
            <div style={{ display: 'flex', gap: '1rem' }}>
                <button 
                  className="btn secondary" 
                  onClick={() => { setReport(null); setFile(null); setLoadingStep(0); setEpsilon(""); setConditionalBy(""); setSmartPii(false); setAutoClean(false); setShowConfig(false); }}
                >
                  New Analysis
                </button>
                <button className="btn secondary" onClick={downloadJson}>
                  <Download size={16} /> JSON Report
                </button>
                <button className="btn" onClick={downloadCsv}>
                  <Download size={16} /> Download CSV
                </button>
            </div>
          </div>

          <div className="results-grid">
            
            {/* Row 1: Profile and Privacy */}
            <div className="grid-row">
                <div className="glass-panel">
                  <h3><Database size={18} /> Dataset Profile</h3>
                  <div style={{ display: 'flex', gap: '2rem', marginBottom: '1.5rem' }}>
                     <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Rows</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{report.dataset.rows}</div>
                     </div>
                     <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Columns</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>{report.dataset.columns}</div>
                     </div>
                  </div>

                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      <table>
                          <thead>
                              <tr>
                                  <th>Column</th>
                                  <th>Type</th>
                                  <th>Missing %</th>
                                  <th>Mean / Unique</th>
                              </tr>
                          </thead>
                          <tbody>
                              {report.schema_profile && report.schema_profile.map((col, idx) => (
                                  <tr key={idx}>
                                      <td style={{ fontWeight: 500, color: 'var(--text-main)' }}>{col.column}</td>
                                      <td><span className="badge">{col.type}</span></td>
                                      <td>{formatNum(col.missing_pct, 1)}%</td>
                                      <td style={{ color: 'var(--text-muted)' }}>
                                          {col.type === 'numeric' ? (
                                              col.is_primary_key ? <span style={{ color: 'var(--warning)' }}>Primary Key</span> : `μ: ${formatNum(col.mean, 2)}`
                                          ) : (
                                              col.semantic_type ? <span style={{ color: 'var(--success)' }}>Faker: {col.semantic_type}</span> :
                                              col.is_primary_key ? <span style={{ color: 'var(--warning)' }}>Primary Key</span> : `${col.unique} unique`
                                          )}
                                      </td>
                                  </tr>
                              ))}
                          </tbody>
                      </table>
                  </div>
                </div>

                <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
                  <h3><ShieldAlert size={18} /> Privacy Alerts</h3>
                  {report.privacy_alerts.length === 0 ? (
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Check size={16} style={{ color: 'var(--success)' }} /> No PII or strict identifiers detected.
                      </p>
                    </div>
                  ) : (
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                      {report.privacy_alerts.map((alert, idx) => (
                        <div key={idx} className="warning-item">
                          <AlertTriangle size={18} style={{ color: alert.level === 'HIGH-CARDINALITY' ? 'var(--danger)' : 'var(--warning)', flexShrink: 0 }} />
                          <div>
                            <div style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-main)' }}>{alert.column}</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>{alert.reason}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
            </div>

            {/* Row 2: Quality Score and Numeric Distributions */}
            <div className="grid-row">
                <div className="glass-panel svg-progress-container" style={{ flex: 1 }}>
                  <h3 style={{ width: '100%' }}><Activity size={18} /> Quality Score</h3>
                  
                  <svg width="160" height="160" viewBox="0 0 100 100" style={{ margin: '1rem 0' }}>
                    <circle className="svg-circle-bg" cx="50" cy="50" r="40" />
                    <circle 
                      className="svg-circle-progress" 
                      cx="50" 
                      cy="50" 
                      r="40" 
                      strokeDasharray="251.2" 
                      strokeDashoffset={typeof report.quality_score === 'number' ? 251.2 - (251.2 * scoreProgress) / 100 : 251.2}
                    />
                    <text x="50" y="52" className="score-text">{formatNum(report.quality_score, 1)}</text>
                  </svg>
                  
                  <div style={{ marginTop: 'auto', width: '100%' }}>
                     <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Mean Correlation Error</div>
                     <div style={{ fontSize: '1.25rem', fontWeight: 500 }}>
                        {formatNum(report.correlation_error, 4)}
                     </div>
                  </div>
                </div>

                <div className="glass-panel" style={{ flex: 2 }}>
                  <h3><BarChart size={18} /> Numeric Fidelity</h3>
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th style={{ width: '30%' }}>Column</th>
                          <th style={{ width: '20%' }}>KS Dist.</th>
                          <th style={{ width: '25%' }}>Mean Err</th>
                          <th style={{ width: '25%' }}>Median Err</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.numeric_distribution.length === 0 ? (
                          <tr>
                            <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No numeric columns to evaluate.</td>
                          </tr>
                        ) : (
                          report.numeric_distribution.map((stat, idx) => (
                            <tr key={idx}>
                              <td style={{ fontWeight: 500 }}>{stat.column}</td>
                              <td style={{ color: 'var(--text-muted)' }}>{formatNum(stat.ks, 4)}</td>
                              <td>{renderErrorBar(stat.mean_error)}</td>
                              <td>{renderErrorBar(stat.median_error)}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
            </div>

          </div>
        </main>
        </ErrorBoundary>
      )}
    </div>
  );
}

export default App;
