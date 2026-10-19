import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { crashed: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { crashed: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', this.props.name, error, info);
  }

  render() {
    if (this.state.crashed) {
      return (
        <div style={{
          margin: '6rem 2rem 2rem',
          background: 'rgba(229,62,62,0.06)',
          border: '1px solid rgba(229,62,62,0.25)',
          borderRadius: '16px',
          padding: '3rem',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
          <h3 style={{ color: '#FC8181', marginBottom: '0.5rem', fontFamily: 'Playfair Display, serif' }}>
            {this.props.name} — Unavailable
          </h3>
          <p style={{ color: '#8A9BB0', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
            This component encountered an error. All other components are working normally.
          </p>
          <p style={{ color: '#4A5568', fontSize: '0.75rem', marginBottom: '1.5rem' }}>
            {this.state.error?.message}
          </p>
          <button
            onClick={() => this.setState({ crashed: false, error: null })}
            style={{
              background: 'rgba(229,62,62,0.15)',
              border: '1px solid rgba(229,62,62,0.3)',
              color: '#FC8181',
              padding: '0.6rem 1.5rem',
              borderRadius: '8px',
              cursor: 'pointer',
              fontFamily: 'DM Sans, sans-serif',
              fontWeight: 600,
            }}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;