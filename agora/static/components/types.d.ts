/**
 * TypeScript type definitions for DHARMIC_AGORA components
 *
 * @packageDocumentation
 */

import { ReactNode } from 'react';

// ============================================================================
// FeatureCard
// ============================================================================

export interface FeatureCardProps {
  /** Icon component or emoji */
  icon: ReactNode;
  /** Feature title */
  title: string;
  /** Feature description */
  description: string;
  /** Whether to highlight this card */
  highlight?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function FeatureCard(props: FeatureCardProps): JSX.Element;

// ============================================================================
// SecurityBadge
// ============================================================================

export type BadgeVariant = 'stat' | 'certification' | 'comparison';

export interface SecurityBadgeProps {
  /** Badge style variant */
  variant?: BadgeVariant;
  /** Badge label text */
  label: string;
  /** Main value to display */
  value: string | number;
  /** Icon or emoji */
  icon?: string;
  /** Whether this is a positive security indicator */
  positive?: boolean;
  /** Optional subtitle text */
  subtitle?: string;
  /** For comparison variant - what to compare against */
  compareWith?: string;
  /** Additional CSS classes */
  className?: string;
}

export function SecurityBadge(props: SecurityBadgeProps): JSX.Element;

export interface SecurityBadgeGridProps {
  children: ReactNode;
  className?: string;
}

export function SecurityBadgeGrid(props: SecurityBadgeGridProps): JSX.Element;

// ============================================================================
// HowItWorks
// ============================================================================

export interface Step {
  /** Step number (1-4) */
  number: number;
  /** Step title */
  title: string;
  /** Step description */
  description: string;
  /** Step icon/emoji */
  icon: string;
  /** Optional code snippet */
  code?: string;
}

export interface HowItWorksProps {
  /** Custom steps (optional) */
  steps?: Step[];
  /** Enable step animation on scroll */
  animated?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function HowItWorks(props: HowItWorksProps): JSX.Element;

export interface HowItWorksCompactProps {
  steps?: Step[];
  className?: string;
}

export function HowItWorksCompact(props: HowItWorksCompactProps): JSX.Element;

// ============================================================================
// CodeDemo
// ============================================================================

export type Language = 'bash' | 'python' | 'javascript' | 'json' | 'curl';

export interface CodeExample {
  /** Tab label */
  label: string;
  /** Programming language */
  language: Language;
  /** Code content */
  code: string;
}

export interface CodeDemoProps {
  /** Demo title */
  title?: string;
  /** Multiple code examples (tabs) */
  examples?: CodeExample[];
  /** Single code snippet (no tabs) */
  code?: string;
  /** Language for single snippet */
  language?: Language;
  /** Show line numbers */
  showLineNumbers?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function CodeDemo(props: CodeDemoProps): JSX.Element;

// ============================================================================
// StatsCounter
// ============================================================================

export interface Stat {
  /** Numeric value to display */
  value: number;
  /** Stat label */
  label: string;
  /** Value prefix (e.g., "$", "#") */
  prefix?: string;
  /** Value suffix (e.g., "%", "ms", "K") */
  suffix?: string;
  /** Highlight this stat */
  highlight?: boolean;
  /** Icon or emoji */
  icon?: string;
  /** Optional description */
  description?: string;
}

export interface StatsCounterProps {
  /** Target value to count to */
  value: number;
  /** Counter label */
  label: string;
  /** Value prefix */
  prefix?: string;
  /** Value suffix */
  suffix?: string;
  /** Animation duration in ms */
  duration?: number;
  /** Enable counting animation */
  animate?: boolean;
  /** Highlight styling */
  highlight?: boolean;
  /** Icon or emoji */
  icon?: string;
  /** Optional description */
  description?: string;
  /** Additional CSS classes */
  className?: string;
}

export function StatsCounter(props: StatsCounterProps): JSX.Element;

export interface StatsGridProps {
  stats: Stat[];
  columns?: number;
  className?: string;
}

export function StatsGrid(props: StatsGridProps): JSX.Element;

/** Pre-configured stats for DHARMIC_AGORA */
export const AGORA_STATS: Stat[];
