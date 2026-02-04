/**
 * StatsCounter.jsx
 *
 * Animated statistics counter with smooth counting animation.
 * Perfect for displaying key metrics like gates, uptime, throughput, etc.
 *
 * @component
 * @example
 * <StatsCounter
 *   value={0}
 *   label="API Keys Stored"
 *   suffix=""
 *   highlight={true}
 * />
 */

import React, { useState, useEffect, useRef } from 'react';

/**
 * @typedef {Object} Stat
 * @property {number} value - Numeric value to display
 * @property {string} label - Stat label
 * @property {string} [prefix] - Value prefix (e.g., "$", "#")
 * @property {string} [suffix] - Value suffix (e.g., "%", "ms", "K")
 * @property {boolean} [highlight] - Highlight this stat
 * @property {string} [icon] - Icon or emoji
 * @property {string} [description] - Optional description
 */

/**
 * @typedef {Object} StatsCounterProps
 * @property {number} value - Target value to count to
 * @property {string} label - Counter label
 * @property {string} [prefix] - Value prefix
 * @property {string} [suffix] - Value suffix
 * @property {number} [duration] - Animation duration in ms
 * @property {boolean} [animate] - Enable counting animation
 * @property {boolean} [highlight] - Highlight styling
 * @property {string} [icon] - Icon or emoji
 * @property {string} [description] - Optional description
 * @property {string} [className] - Additional CSS classes
 */

/**
 * Easing function for smooth animation
 */
function easeOutQuad(t) {
  return t * (2 - t);
}

/**
 * Format number with commas
 */
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * StatsCounter component
 * @param {StatsCounterProps} props
 */
export default function StatsCounter({
  value,
  label,
  prefix = '',
  suffix = '',
  duration = 2000,
  animate = true,
  highlight = false,
  icon,
  description,
  className = ''
}) {
  const [displayValue, setDisplayValue] = useState(animate ? 0 : value);
  const [isVisible, setIsVisible] = useState(false);
  const [hasAnimated, setHasAnimated] = useState(false);
  const counterRef = useRef(null);

  useEffect(() => {
    if (!animate || hasAnimated) {
      setDisplayValue(value);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.5 }
    );

    if (counterRef.current) {
      observer.observe(counterRef.current);
    }

    return () => observer.disconnect();
  }, [animate, hasAnimated, value]);

  useEffect(() => {
    if (!isVisible || hasAnimated) return;

    const startTime = Date.now();
    const startValue = 0;
    const endValue = value;

    const animateCounter = () => {
      const now = Date.now();
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const easedProgress = easeOutQuad(progress);
      const currentValue = Math.floor(startValue + (endValue - startValue) * easedProgress);

      setDisplayValue(currentValue);

      if (progress < 1) {
        requestAnimationFrame(animateCounter);
      } else {
        setHasAnimated(true);
      }
    };

    requestAnimationFrame(animateCounter);
  }, [isVisible, value, duration, hasAnimated]);

  return (
    <div
      ref={counterRef}
      className={`
        stats-counter
        ${highlight ? 'stats-counter--highlight' : ''}
        ${className}
      `}
      role="status"
      aria-live="polite"
    >
      {icon && (
        <div className="stats-counter__icon" aria-hidden="true">
          {icon}
        </div>
      )}

      <div className="stats-counter__content">
        <div className="stats-counter__value">
          <span className="stats-counter__prefix">{prefix}</span>
          <span className="stats-counter__number">
            {formatNumber(displayValue)}
          </span>
          <span className="stats-counter__suffix">{suffix}</span>
        </div>

        <div className="stats-counter__label">
          {label}
        </div>

        {description && (
          <div className="stats-counter__description">
            {description}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * StatsGrid component - Grid layout for multiple stats
 */
export function StatsGrid({ stats, columns = 3, className = '' }) {
  return (
    <div
      className={`stats-grid stats-grid--cols-${columns} ${className}`}
      role="region"
      aria-label="Statistics"
    >
      {stats.map((stat, index) => (
        <StatsCounter
          key={index}
          value={stat.value}
          label={stat.label}
          prefix={stat.prefix}
          suffix={stat.suffix}
          highlight={stat.highlight}
          icon={stat.icon}
          description={stat.description}
        />
      ))}
    </div>
  );
}

/**
 * Pre-configured stats for DHARMIC_AGORA
 */
export const AGORA_STATS = [
  {
    value: 0,
    label: 'API Keys Stored',
    icon: '🔒',
    highlight: true,
    description: 'Only Ed25519 public keys'
  },
  {
    value: 17,
    label: 'Verification Gates',
    icon: '⛩️',
    highlight: false,
    description: 'Dharmic content filters'
  },
  {
    value: 5456,
    label: 'Lines of Code',
    icon: '💻',
    highlight: false,
    description: 'Not vaporware'
  },
  {
    value: 99.9,
    label: 'Uptime',
    suffix: '%',
    icon: '⚡',
    highlight: false,
    description: 'Production ready'
  },
  {
    value: 100,
    label: 'Tamper Detection',
    suffix: '%',
    icon: '🔗',
    highlight: true,
    description: 'Chained audit trail'
  },
  {
    value: 0,
    label: 'Remote Code Execution',
    icon: '🛡️',
    highlight: true,
    description: 'Pull-only architecture'
  }
];

/**
 * TypeScript type definitions
 */
export const StatsCounterTypes = `
interface Stat {
  value: number;
  label: string;
  prefix?: string;
  suffix?: string;
  highlight?: boolean;
  icon?: string;
  description?: string;
}

interface StatsCounterProps {
  value: number;
  label: string;
  prefix?: string;
  suffix?: string;
  duration?: number;
  animate?: boolean;
  highlight?: boolean;
  icon?: string;
  description?: string;
  className?: string;
}

interface StatsGridProps {
  stats: Stat[];
  columns?: number;
  className?: string;
}
`;

/**
 * CSS Module styles
 */
export const styles = `
.stats-counter {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  border-radius: 12px;
  background: white;
  border: 2px solid #e5e7eb;
  transition: all 0.3s ease;
  text-align: center;
}

.stats-counter:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: #d1d5db;
}

.stats-counter--highlight {
  border: 2px solid #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.stats-counter--highlight .stats-counter__value {
  color: #059669;
}

.stats-counter__icon {
  font-size: 3rem;
  line-height: 1;
  opacity: 0.9;
}

.stats-counter__content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.stats-counter__value {
  font-size: 3rem;
  font-weight: 800;
  color: #1f2937;
  line-height: 1;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.stats-counter__prefix,
.stats-counter__suffix {
  font-size: 1.5rem;
  font-weight: 600;
  opacity: 0.7;
}

.stats-counter__number {
  display: inline-block;
  min-width: 2ch;
}

.stats-counter__label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stats-counter__description {
  font-size: 0.813rem;
  color: #9ca3af;
  line-height: 1.4;
  margin-top: 0.25rem;
}

/* Grid layout */
.stats-grid {
  display: grid;
  gap: 1.5rem;
  width: 100%;
}

.stats-grid--cols-2 {
  grid-template-columns: repeat(2, 1fr);
}

.stats-grid--cols-3 {
  grid-template-columns: repeat(3, 1fr);
}

.stats-grid--cols-4 {
  grid-template-columns: repeat(4, 1fr);
}

/* Responsive */
@media (max-width: 1024px) {
  .stats-grid--cols-4 {
    grid-template-columns: repeat(2, 1fr);
  }

  .stats-grid--cols-3 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-counter {
    padding: 1.5rem;
  }

  .stats-counter__icon {
    font-size: 2.5rem;
  }

  .stats-counter__value {
    font-size: 2.5rem;
  }

  .stats-counter__prefix,
  .stats-counter__suffix {
    font-size: 1.25rem;
  }

  .stats-grid {
    grid-template-columns: 1fr !important;
  }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .stats-counter {
    background: #1f2937;
    border-color: #374151;
  }

  .stats-counter--highlight {
    background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
    border-color: #10b981;
  }

  .stats-counter__value {
    color: #f9fafb;
  }

  .stats-counter--highlight .stats-counter__value {
    color: #10b981;
  }

  .stats-counter__label {
    color: #d1d5db;
  }

  .stats-counter__description {
    color: #9ca3af;
  }
}

/* Animation for highlight pulse */
@keyframes pulse-highlight {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
  }
}

.stats-counter--highlight:hover {
  animation: pulse-highlight 2s infinite;
}

/* Loading state */
.stats-counter--loading .stats-counter__value {
  opacity: 0.5;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .stats-counter {
    transition: none;
  }

  .stats-counter:hover {
    transform: none;
  }

  .stats-counter--highlight:hover {
    animation: none;
  }
}
`;
