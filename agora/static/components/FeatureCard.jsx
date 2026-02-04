/**
 * FeatureCard.jsx
 *
 * Displays a feature with icon, title, and description.
 * Responsive, accessible, and supports hover states.
 *
 * @component
 * @example
 * <FeatureCard
 *   icon={<ShieldIcon />}
 *   title="Ed25519 Authentication"
 *   description="No API keys in database - cryptographic signatures only"
 *   highlight={true}
 * />
 */

import React from 'react';

/**
 * @typedef {Object} FeatureCardProps
 * @property {React.ReactNode} icon - Icon component or emoji
 * @property {string} title - Feature title
 * @property {string} description - Feature description
 * @property {boolean} [highlight] - Whether to highlight this card
 * @property {string} [className] - Additional CSS classes
 */

/**
 * FeatureCard component
 * @param {FeatureCardProps} props
 */
export default function FeatureCard({
  icon,
  title,
  description,
  highlight = false,
  className = ''
}) {
  return (
    <div
      className={`
        feature-card
        ${highlight ? 'feature-card--highlight' : ''}
        ${className}
      `}
      role="article"
      aria-labelledby={`feature-${title.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="feature-card__icon" aria-hidden="true">
        {icon}
      </div>

      <h3
        id={`feature-${title.toLowerCase().replace(/\s+/g, '-')}`}
        className="feature-card__title"
      >
        {title}
      </h3>

      <p className="feature-card__description">
        {description}
      </p>
    </div>
  );
}

/**
 * TypeScript type definitions (for .tsx version)
 */
export const FeatureCardTypes = `
interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  highlight?: boolean;
  className?: string;
}
`;

/**
 * CSS Module styles (example)
 */
export const styles = `
.feature-card {
  padding: 2rem;
  border-radius: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #d1d5db;
}

.feature-card--highlight {
  border: 2px solid #8b5cf6;
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
}

.feature-card__icon {
  font-size: 2.5rem;
  line-height: 1;
  color: #8b5cf6;
}

.feature-card--highlight .feature-card__icon {
  color: #7c3aed;
}

.feature-card__title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
  line-height: 1.4;
}

.feature-card__description {
  font-size: 0.95rem;
  color: #6b7280;
  line-height: 1.6;
  margin: 0;
  flex-grow: 1;
}

/* Responsive */
@media (max-width: 768px) {
  .feature-card {
    padding: 1.5rem;
  }

  .feature-card__icon {
    font-size: 2rem;
  }

  .feature-card__title {
    font-size: 1.125rem;
  }

  .feature-card__description {
    font-size: 0.875rem;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .feature-card {
    background: #1f2937;
    border-color: #374151;
  }

  .feature-card--highlight {
    background: linear-gradient(135deg, #2d1b4e 0%, #3b2667 100%);
    border-color: #8b5cf6;
  }

  .feature-card__title {
    color: #f9fafb;
  }

  .feature-card__description {
    color: #d1d5db;
  }
}
`;
