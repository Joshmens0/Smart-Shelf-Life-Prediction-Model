import React from 'react';
import { Apple, Cpu, Sliders, GraduationCap, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { requireAuth } = useAuth();

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <header style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.03em' }}>
          Model <span className="gradient-text">Configuration</span>
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Explore neural network hyper-parameters, data boundaries, and project context.
        </p>
      </header>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        {/* Project Context */}
        <section className="card" style={{ display: 'flex', gap: '20px' }}>
          <div style={{
            background: 'rgba(34, 211, 238, 0.1)',
            padding: '16px',
            borderRadius: '50%',
            color: 'var(--accent-cyan)',
            alignSelf: 'flex-start',
            display: 'flex'
          }}>
            <GraduationCap size={32} />
          </div>
          <div style={{ flex: 1 }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '8px' }}>University Project Profile</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '12px' }}>
              This multimodal shelf life prediction webapp is developed as a final year project at the
              <strong> University of Ghana</strong>. It implements an advanced deep learning architecture merging computer vision
              and sensory metadata to solve food waste tracking on smart kitchen shelves and commercial storage pantries.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <span>🏫 <strong>Institution:</strong> University of Ghana</span>
              <span>🎓 <strong>Department:</strong>Food Process Engineering</span>
            </div>
          </div>
        </section>

        {/* Model info details */}
        <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '10px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <Cpu size={20} color="var(--accent-cyan)" />
            Neural Network Abstractions
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Image Backbone */}
            <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Apple size={16} color="var(--accent-green)" /> Image Backbone
              </h4>
              <ul style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', listStyleType: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <li>🧬 <strong>CNN Model:</strong> EfficientNet-B0</li>
                <li>🎯 <strong>Input Size:</strong> 224 × 224 RGB image</li>
                <li>🔢 <strong>Output Embedding:</strong> 256 vector</li>
                <li>❄️ <strong>Weights:</strong> Pre-trained ImageNet-1K</li>
              </ul>
            </div>

            {/* Tabular Branch */}
            <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sliders size={16} color="var(--accent-blue)" /> Tabular MLP Branch
              </h4>
              <ul style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', listStyleType: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <li>⚙️ <strong>Numerical Inputs:</strong> Temp (°C), Humidity (%)</li>
                <li>🏷️ <strong>Categorical:</strong> Environment (Ambient, Controlled)</li>
                <li>📈 <strong>Embedding Dimension:</strong> 4 dimension (Env mapping)</li>
                <li>⛓️ <strong>MLP Dimensions:</strong> Output embedding 128 vector</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Server Config settings */}
        <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '10px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <ShieldCheck size={20} color="var(--accent-green)" />
            Server Security Settings
          </h3>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <tbody>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontWeight: 600 }}>Optional Authentication (Toggled)</td>
                <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                  <span className="badge badge-green" style={{ textTransform: 'capitalize' }}>
                    {requireAuth ? "JWT active" : "Demo bypass mode"}
                  </span>
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontWeight: 600 }}>Default Database dialect</td>
                <td style={{ padding: '12px 8px', textAlign: 'right', fontFamily: 'monospace' }}>aiosqlite (SQLite Async)</td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontWeight: 600 }}>Temporary Directory uploads caching</td>
                <td style={{ padding: '12px 8px', textAlign: 'right', fontFamily: 'monospace' }}>webapp/backend/tmp/uploads/</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
};
export default SettingsPage;
