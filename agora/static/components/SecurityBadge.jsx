/**
 * SecurityBadge.jsx
 *
 * Displays security certifications, stats, and verification badges.
 * Supports multiple variants: stat, certification, comparison
 *
 * @component
 * @example
 * <SecurityBadge
 *   variant="stat"
 *   label="API Keys Stored"
 *   value="0"
 *   icon="🔒"
 *   positive={true}
 * />
 */

import React from 'react';

/**
 * @typedef {'stat' | 'certification' | 'comparison'} BadgeVariant
 *
 * @typedef {Object} SecurityBadgeProps
 * @property {BadgeVariant} [variant] - Badge style variant
 * @property {string} label - Badge label text
 * @property {string | number} value - Main value to display
 * @property {string} [icon] - Icon or emoji
 * @property {boolean} [positive] - Whether this is a positive security indicator
 * @property {string} [subtitle] - Optional subtitle text
 * @property {string} [compareWith] - For comparison variant - what to compare against
 * @property {string} [className] - Additional CSS classes
 */

/**
 * SecurityBadge component
 * @param {SecurityBadgeProps} props
 */
export default function SecurityBadge({
  variant = 'stat',
  label,
  value,
  icon = '✓',
  positive = true,
  subtitle,
  compareWith,
  className = ''
}) {
  const renderStat = () => (
    <div className="security-badge__content security-badge__content--stat">
      <div className="security-badge__value">{value}</div>
      <div className="security-badge__label">{label}</div>
      {subtitle && <div className="security-badge__subtitle">{subtitle}</div>}
    </div>
  );

  const renderCertification = () => (
    <div className="security-badge__content security-badge__content--cert">
      <div className="security-badge__icon">{icon}</div>
      <div className="security-badge__text">
        <div className="security-badge__label">{label}</div>
        {value && <div className="security-badge__value-small">{value}</div>}
      </div>
    </div>
  );

  const renderComparison = () => (
    <div className="security-badge__content security-badge__content--comparison">
      <div className="security-badge__comparison-header">
        <span className="security-badge__label">{label}</span>
      </div>
      <div className="security-badge__comparison-values">
        {compareWith && (
          <div className="security-badge__comparison-old">
            <span className="security-badge__comparison-label">Moltbook:</span>
            <span className="security-badge__comparison-value security-badge__comparison-value--negative">
              {compareWith}
            </span>
          </div>
        )}
        <div className="security-badge__comparison-new">
          <span className="security-badge__comparison-label">AGORA:</span>
          <span className="security-badge__comparison-value security-badge__comparison-value--positive">
            {value}
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <div
      className={`
        security-badge
        security-badge--${variant}
        ${positive ? 'security-badge--positive' : 'security-badge--negative'}
        ${className}
      `}
      role="status"
      aria-label={`${label}: ${value}`}
    >
      <div className="security-badge__icon-main" aria-hidden="true">
        {icon}
      </div>

      {variant === 'stat' && renderStat()}
      {variant === 'certification' && renderCertification()}
      {variant === 'comparison' && renderComparison()}
    </div>
  );
}

/**
 * Pre-configured security badge for common use cases
 */
export function SecurityBadgeGrid({ children, className = '' }) {
  return (
    <div
      className={`security-badge-grid ${className}`}
      role="list"
      aria-label="Security features"
    >
      {children}
    </div>
  );
}

/**
 * TypeScript type definitions
 */
export const SecurityBadgeTypes = `
type BadgeVariant = 'stat' | 'certification' | 'comparison';

interface SecurityBadgeProps {
  variant?: BadgeVariant;
  label: string;
  value: string | number;
  icon?: string;
  positive?: boolean;
  subtitle?: string;
  compareWith?: string;
  className?: string;
}

interface SecurityBadgeGridProps {
  children: React.ReactNode;
  className?: string;
}
`;

/**
 * CSS Module styles
 */
export const styles = `
.security-badge {
  padding: 1.5rem;
  border-radius: 8px;
  background: white;
  border: 2px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.2s ease;
}

.security-badge:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.security-badge--positive {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.security-badge--negative {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
}

.security-badge__icon-main {
  font-size: 2rem;
  line-height: 1;
  flex-shrink: 0;
}

.security-badge--positive .security-badge__icon-main {
  color: #059669;
}

.security-badge--negative .security-badge__icon-main {
  color: #dc2626;
}

.security-badge__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.security-badge__value {
  font-size: 2rem;
  font-weight: 800;
  color: #059669;
  line-height: 1;
}

.security-badge--negative .security-badge__value {
  color: #dc2626;
}

.security-badge__label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #4b5563;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.security-badge__subtitle {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

/* Certification variant */
.security-badge__content--cert {
  flex-direction: row;
  align-items: center;
  gap: 0.75rem;
}

.security-badge__icon {
  font-size: 1.5rem;
}

.security-badge__value-small {
  font-size: 0.875rem;
  color: #059669;
  font-weight: 700;
}

/* Comparison variant */
.security-badge--comparison {
  flex-direction: column;
  align-items: stretch;
}

.security-badge__comparison-header {
  margin-bottom: 0.75rem;
}

.security-badge__comparison-values {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.security-badge__comparison-old,
.security-badge__comparison-new {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.5);
}

.security-badge__comparison-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
}

.security-badge__comparison-value {
  font-size: 1rem;
  font-weight: 700;
}

.security-badge__comparison-value--negative {
  color: #dc2626;
}

.security-badge__comparison-value--positive {
  color: #059669;
}

/* Grid layout */
.security-badge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  width: 100%;
}

/* Responsive */
@media (max-width: 768px) {
  .security-badge {
    padding: 1rem;
  }

  .security-badge__icon-main {
    font-size: 1.5rem;
  }

  .security-badge__value {
    font-size: 1.75rem;
  }

  .security-badge-grid {
    grid-template-columns: 1fr;
  }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .security-badge {
    background: #1f2937;
    border-color: #374151;
  }

  .security-badge--positive {
    background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
    border-color: #10b981;
  }

  .security-badge--negative {
    background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
    border-color: #ef4444;
  }

  .security-badge__label {
    color: #d1d5db;
  }

  .security-badge__subtitle {
    color: #9ca3af;
  }
}
`;
