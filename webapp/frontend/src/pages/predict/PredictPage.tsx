import React, { useState, useRef } from 'react';
import ProgressGauge from '../../components/ui/ProgressGauge';
import { Upload, Thermometer, Droplets, Info, AlertCircle, ArrowRight } from 'lucide-react';

const CATEGORY_PRESETS = [
  { id: 'mango', label: 'Mango' },
  { id: 'tomato', label: 'Tomato' },
  { id: 'banana', label: 'Banana' },
  { id: 'avocado', label: 'Avocado' },
  { id: 'apple', label: 'Apple' },
  { id: 'other', label: 'Other Fresh Produce' }
];

export const PredictPage: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form parameters state
  const [itemName, setItemName] = useState('');
  const [category, setCategory] = useState('mango');
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [temp, setTemp] = useState(25.0);
  const [humidity, setHumidity] = useState(65.0);
  const [environment, setEnvironment] = useState<'ambient' | 'controlled'>('ambient');

  // Request execution state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const selectPresetCategory = (id: string, label: string) => {
    setCategory(id);
    if (!itemName) {
      setItemName(label);
    }
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!image) {
      setError("Please upload or drag a photo of the item first.");
      return;
    }
    if (!itemName.trim()) {
      setError("Please enter a name/label for the item.");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('image', image);
    formData.append('temp', temp.toString());
    formData.append('humidity', humidity.toString());
    formData.append('environment', environment);
    formData.append('item_name', itemName.trim() || category);

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error?.message || "Prediction execution failed");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to contact prediction server.");
    } finally {
      setLoading(false);
    }
  };

  // Helper to suggest storage improvements
  const getRecommendation = () => {
    if (!result) return null;
    const days = result.days_remaining;

    if (days < 2.0) {
      return {
        title: "Immediate Consumption Required",
        desc: `This item is showing signs of critical degradation. Consume immediately or transfer to freezing storage to prevent spoilage.`,
        action: "Consume or Freeze"
      };
    } else if (days <= 5.0) {
      if (result.environment === 'ambient') {
        return {
          title: "Move to Controlled Storage",
          desc: `Current ambient shelf life is limited. Moving this item to controlled refrigeration (~10°C, 85% RH) can extend its shelf life by up to 2-3x.`,
          action: "Move to Cold Room"
        };
      }
      return {
        title: "Monitor Closely",
        desc: `Item is in cold storage but approaching expiration. Ensure humidity remains stable to avoid surface mold formation.`,
        action: "Stable controlled room"
      };
    } else {
      if (result.environment === 'ambient') {
        return {
          title: "Fresh Status Stable",
          desc: `Item is stable at ambient. If storage duration needs to be extended, refrigerating will maximize shelf life stability.`,
          action: "Ambient stable"
        };
      }
      return {
        title: "Optimal Cold Chain Maintenance",
        desc: `Freshness is excellent under controlled conditions. Maintain current environment setup for maximum longevity.`,
        action: "Maintain environment"
      };
    }
  };

  const rec = getRecommendation();

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.03em' }}>
          Smart Freshness <span className="gradient-text">Predictor</span>
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Upload a photo and input sensor values to predict remaining shelf life.
        </p>
      </header>

      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid var(--accent-red)',
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-red)',
          display: 'flex',
          gap: '12px',
          marginBottom: '32px',
          alignItems: 'center'
        }}>
          <AlertCircle size={20} />
          <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{error}</span>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', alignItems: 'start' }}>
        {/* Left Side Inputs Form */}
        <form onSubmit={handlePredict} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            Input Measurements
          </h3>

          {/* Item Name */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Item Name / Label
            </label>
            <input
              type="text"
              className="input"
              placeholder="e.g. Mango Batch A, Organic Tomatoes"
              value={itemName}
              onChange={(e) => setItemName(e.target.value)}
              required
            />
          </div>

          {/* Preset buttons */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Category Selection
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {CATEGORY_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => selectPresetCategory(preset.id, preset.label)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: category === preset.id ? 'var(--gradient-primary)' : 'var(--bg-tertiary)',
                    color: category === preset.id ? 'var(--text-on-accent)' : 'var(--text-secondary)',
                    border: '1px solid var(--border-subtle)',
                    transition: 'all var(--transition-fast)'
                  }}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Image Uploader */}
          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: '2px dashed var(--border-medium)',
              borderRadius: 'var(--radius-lg)',
              padding: '32px 16px',
              textAlign: 'center',
              cursor: 'pointer',
              background: 'var(--bg-tertiary)',
              transition: 'all var(--transition-fast)',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageChange}
              accept="image/*"
              style={{ display: 'none' }}
            />
            {imagePreview ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <img
                  src={imagePreview}
                  alt="Upload preview"
                  style={{
                    maxHeight: '160px',
                    borderRadius: 'var(--radius-md)',
                    objectFit: 'cover',
                    marginBottom: '12px',
                    boxShadow: 'var(--shadow-sm)'
                  }}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Click to replace photo ({image?.name})
                </span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                <Upload size={32} style={{ color: 'var(--accent-cyan)' }} />
                <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Drag & drop product photo here
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  or click to browse local files (PNG, JPG, WEBP)
                </span>
              </div>
            )}
          </div>

          {/* Sliders Container */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Temp Slider */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Thermometer size={14} /> Temp
                </span>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>{temp.toFixed(1)}°C</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="50.0"
                step="0.5"
                value={temp}
                onChange={(e) => setTemp(parseFloat(e.target.value))}
              />
            </div>

            {/* Humidity Slider */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Droplets size={14} /> Humidity
                </span>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>{humidity.toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="10.0"
                max="100.0"
                step="1.0"
                value={humidity}
                onChange={(e) => setHumidity(parseFloat(e.target.value))}
              />
            </div>
          </div>

          {/* Environment */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Storage Environment
            </label>
            <div style={{
              display: 'flex',
              background: 'var(--bg-tertiary)',
              padding: '4px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)'
            }}>
              <button
                type="button"
                onClick={() => setEnvironment('ambient')}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  background: environment === 'ambient' ? 'var(--bg-card)' : 'transparent',
                  color: environment === 'ambient' ? 'var(--text-primary)' : 'var(--text-secondary)',
                  border: environment === 'ambient' ? '1px solid var(--border-medium)' : '1px solid transparent',
                  transition: 'all var(--transition-fast)'
                }}
              >
                Ambient (Room Temp)
              </button>
              <button
                type="button"
                onClick={() => setEnvironment('controlled')}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  background: environment === 'controlled' ? 'var(--bg-card)' : 'transparent',
                  color: environment === 'controlled' ? 'var(--text-primary)' : 'var(--text-secondary)',
                  border: environment === 'controlled' ? '1px solid var(--border-medium)' : '1px solid transparent',
                  transition: 'all var(--transition-fast)'
                }}
              >
                Controlled (Cold Room)
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%', padding: '14px', fontSize: '1rem', marginTop: '8px' }}
          >
            {loading ? 'Running AI Model Inference...' : 'Predict Shelf Life'}
          </button>
        </form>

        {/* Right Side Result Visual Dashboard */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {loading ? (
            <div className="card" style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '400px',
              gap: '24px'
            }}>
              <div style={{
                width: '50px',
                height: '50px',
                border: '4px solid var(--border-medium)',
                borderTopColor: 'var(--accent-cyan)',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              <div style={{ textAlign: 'center' }}>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Processing Multimodal Inputs</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '6px' }}>
                  Extracting visual features (CNN) & compiling tabular measurements (MLP)...
                </p>
              </div>
            </div>
          ) : result ? (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '28px', animation: 'fadeIn 0.5s ease' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
                Freshness Report: <span style={{ color: 'var(--accent-cyan)' }}>{result.item_name}</span>
              </h3>

              {/* Progress dial circular gauge */}
              <ProgressGauge value={result.days_remaining} environment={result.environment} />

              <div style={{
                background: 'var(--bg-tertiary)',
                padding: '20px',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-medium)'
              }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Info size={16} color="var(--accent-cyan)" />
                  AI Recommendation
                </h4>
                <h5 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  {rec?.title}
                </h5>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {rec?.desc}
                </p>
              </div>

              {/* Projections comparative metrics */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
                  Environmental Sensor Parameters logged:
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div style={{ background: 'var(--bg-glass)', border: '1px solid var(--border-subtle)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', display: 'block' }}>Logged Temp</span>
                    <span style={{ fontSize: '1.1rem', fontWeight: 700 }}>{result.temperature}°C</span>
                  </div>
                  <div style={{ background: 'var(--bg-glass)', border: '1px solid var(--border-subtle)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', display: 'block' }}>Logged Humidity</span>
                    <span style={{ fontSize: '1.1rem', fontWeight: 700 }}>{result.humidity}%</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card" style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '400px',
              textAlign: 'center',
              padding: '40px',
              border: '2px dashed var(--border-subtle)'
            }}>
              <div style={{
                background: 'rgba(34, 211, 238, 0.05)',
                padding: '20px',
                borderRadius: '50%',
                marginBottom: '20px'
              }}>
                <ArrowRight size={36} style={{ color: 'var(--accent-cyan)' }} />
              </div>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Awaiting Measurements</h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '300px', marginTop: '8px', lineHeight: 1.5 }}>
                Fill out the sensor fields on the left and submit to initiate shelf life estimation.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default PredictPage;
