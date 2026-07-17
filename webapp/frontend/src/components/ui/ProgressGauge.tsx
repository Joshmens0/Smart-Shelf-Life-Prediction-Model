import React from 'react';

interface ProgressGaugeProps {
  value: number;       // days remaining (e.g. 4.2)
  environment: string; // "ambient" | "controlled"
}

export const ProgressGauge: React.FC<ProgressGaugeProps> = ({ value, environment }) => {
  // Determine bounds from settings
  const maxDays = environment === 'controlled' ? 21.0 : 7.0;
  
  // Floor/ceiling bounds checking
  const days = Math.max(0.0, Math.min(maxDays, value));
  const percentage = (days / maxDays) * 100;
  
  // SVG Ring Calculations
  const radius = 80;
  const stroke = 12;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  // Determine indicator color classification
  let color = 'var(--accent-green)';
  let label = 'Fresh';
  let gradientId = 'gradient-green';

  if (days < 2.0) {
    color = 'var(--accent-red)';
    label = 'Expired / Critical';
    gradientId = 'gradient-danger';
  } else if (days <= 5.0) {
    color = 'var(--accent-orange)';
    label = 'Expiring Soon';
    gradientId = 'gradient-warning';
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
      position: 'relative'
    }}>
      <div style={{ position: 'relative', width: radius * 2, height: radius * 2 }}>
        <svg
          height={radius * 2}
          width={radius * 2}
          style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
        >
          {/* Gradients declarations */}
          <defs>
            <linearGradient id="gradient-green" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
            <linearGradient id="gradient-warning" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#d97706" />
            </linearGradient>
            <linearGradient id="gradient-danger" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="100%" stopColor="#dc2626" />
            </linearGradient>
          </defs>

          {/* Underlay tracking circle */}
          <circle
            stroke="var(--border-subtle)"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          {/* Active progress indicator ring */}
          <circle
            stroke={`url(#${gradientId})`}
            fill="transparent"
            strokeWidth={stroke}
            strokeDasharray={circumference + ' ' + circumference}
            style={{ strokeDashoffset, transition: 'stroke-dashoffset 0.8s ease-out-in' }}
            strokeLinecap="round"
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            filter={`drop-shadow(0 0 4px ${color})`}
          />
        </svg>

        {/* Digital readouts */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center'
        }}>
          <span style={{
            fontSize: '2.5rem',
            fontWeight: 800,
            lineHeight: 1.1,
            color: 'var(--text-primary)',
            letterSpacing: '-0.03em'
          }}>
            {days.toFixed(1)}
          </span>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Day{days === 1.0 ? '' : 's'} Left
          </span>
        </div>
      </div>

      <div style={{
        marginTop: '20px',
        textAlign: 'center'
      }}>
        <span className="badge" style={{
          background: days < 2.0 ? 'rgba(239, 68, 68, 0.15)' : days <= 5.0 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
          color: color,
          fontSize: '0.85rem',
          padding: '6px 14px',
          boxShadow: `0 0 12px ${color}1a`
        }}>
          {label}
        </span>
      </div>
    </div>
  );
};
export default ProgressGauge;
