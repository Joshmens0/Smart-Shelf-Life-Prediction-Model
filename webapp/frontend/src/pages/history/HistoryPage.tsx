import React, { useState, useEffect } from 'react';
import { Search, Calendar, Thermometer, Droplets, Trash2, ShieldAlert, BarChart3, Database } from 'lucide-react';

export const HistoryPage: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({
    total_items: 0,
    average_shelf_life: 0.0,
    environment_distribution: { ambient: 0, controlled: 0 },
    status_counts: { fresh: 0, warning: 0, expired: 0 }
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filtering states
  const [searchTerm, setSearchTerm] = useState('');
  const [envFilter, setEnvFilter] = useState<'all' | 'ambient' | 'controlled'>('all');

  const fetchData = async () => {
    try {
      // Fetch history list
      const listRes = await fetch('/api/history');
      if (!listRes.ok) throw new Error("Failed to load history list");
      const listData = await listRes.json();
      setItems(listData.items || []);

      // Fetch aggregated metrics stats
      const statsRes = await fetch('/api/stats');
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load database records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this prediction record? This will delete the saved image file too.")) {
      return;
    }

    try {
      const res = await fetch(`/api/history/${id}`, {
        method: 'DELETE'
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error?.message || "Failed to delete record");
      }

      // Update state locally
      setItems(items.filter(item => item.id !== id));
      
      // Refresh stats
      const statsRes = await fetch('/api/stats');
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
    } catch (err: any) {
      alert(err.message || "Failed to delete record.");
    }
  };

  // Filter items
  const filteredItems = items.filter(item => {
    const matchesSearch = item.item_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesEnv = envFilter === 'all' || item.environment === envFilter;
    return matchesSearch && matchesEnv;
  });

  const getStatusBadge = (days: number) => {
    if (days < 2.0) {
      return <span className="badge badge-red">Expired</span>;
    } else if (days <= 5.0) {
      return <span className="badge badge-orange">Warning</span>;
    }
    return <span className="badge badge-green">Fresh</span>;
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: 'var(--text-secondary)' }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '3px solid var(--border-medium)',
          borderTopColor: 'var(--accent-cyan)',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.03em' }}>
          Freshness <span className="gradient-text">Inventory</span>
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Track and review all previous fresh produce predictions.
        </p>
      </header>

      {/* Analytics stats summaries grids */}
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '20px',
        marginBottom: '40px'
      }}>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '20px' }}>
          <div style={{ background: 'rgba(16, 116, 231, 0.1)', padding: '12px', borderRadius: 'var(--radius-md)', color: 'var(--accent-blue)' }}>
            <Database size={24} />
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', fontWeight: 600 }}>Total Monitored</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 800 }}>{stats.total_items} items</span>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '20px' }}>
          <div style={{ background: 'rgba(34, 211, 238, 0.1)', padding: '12px', borderRadius: 'var(--radius-md)', color: 'var(--accent-cyan)' }}>
            <BarChart3 size={24} />
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', fontWeight: 600 }}>Avg Remaining Life</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 800 }}>{stats.average_shelf_life.toFixed(1)} days</span>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '20px' }}>
          <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '12px', borderRadius: 'var(--radius-md)', color: 'var(--accent-green)' }}>
            <Database size={24} />
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', fontWeight: 600 }}>Fresh Items</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-green)' }}>{stats.status_counts.fresh}</span>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '20px' }}>
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '12px', borderRadius: 'var(--radius-md)', color: 'var(--accent-red)' }}>
            <ShieldAlert size={24} />
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', fontWeight: 600 }}>Critical / Expired</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-red)' }}>{stats.status_counts.expired}</span>
          </div>
        </div>
      </section>

      {/* Filters toolbar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        gap: '16px'
      }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
          <span style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)', display: 'flex' }}>
            <Search size={16} />
          </span>
          <input
            type="text"
            className="input"
            placeholder="Search items by label..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ paddingLeft: '44px' }}
          />
        </div>

        {/* Environment Filter tabs */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-card)',
          padding: '4px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)'
        }}>
          {['all', 'ambient', 'controlled'].map((env) => (
            <button
              key={env}
              onClick={() => setEnvFilter(env as any)}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                fontWeight: 600,
                textTransform: 'capitalize',
                background: envFilter === env ? 'var(--bg-tertiary)' : 'transparent',
                color: envFilter === env ? 'var(--text-primary)' : 'var(--text-secondary)',
                border: envFilter === env ? '1px solid var(--border-medium)' : '1px solid transparent',
                transition: 'all var(--transition-fast)'
              }}
            >
              {env}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of history cards */}
      {filteredItems.length === 0 ? (
        <div className="card" style={{
          padding: '60px',
          textAlign: 'center',
          border: '2px dashed var(--border-subtle)'
        }}>
          <p style={{ color: 'var(--text-secondary)' }}>No items found matching your filters.</p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '24px'
        }}>
          {filteredItems.map((item, index) => (
            <div
              key={item.id}
              className="card card-active"
              style={{
                padding: '0',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                '--stagger-index': index
              } as React.CSSProperties}
            >
              {/* Product Thumbnail */}
              <div style={{ position: 'relative', height: '180px', background: '#000' }}>
                <img
                  src={item.image_path}
                  alt={item.item_name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <div style={{ position: 'absolute', top: '12px', right: '12px' }}>
                  {getStatusBadge(item.days_remaining)}
                </div>
              </div>

              {/* Card Body */}
              <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <h4 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0' }}>{item.item_name}</h4>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
                    <Calendar size={12} />
                    {formatDate(item.created_at)}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)', padding: '12px 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    <Thermometer size={14} style={{ color: 'var(--accent-blue)' }} />
                    {item.temperature.toFixed(1)}°C
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    <Droplets size={14} style={{ color: 'var(--accent-cyan)' }} />
                    {item.humidity.toFixed(0)}%
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                  <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', display: 'block', fontWeight: 600 }}>Remaining Life</span>
                    <span style={{ fontSize: '1.2rem', fontWeight: 800 }}>{item.days_remaining.toFixed(1)} days</span>
                  </div>
                  
                  <button
                    onClick={() => handleDelete(item.id)}
                    style={{
                      padding: '8px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(239, 68, 68, 0.1)',
                      color: 'var(--accent-red)',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)'
                    }}
                    title="Delete record"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default HistoryPage;
