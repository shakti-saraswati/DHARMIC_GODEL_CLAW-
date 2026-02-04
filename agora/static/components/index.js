/**
 * DHARMIC_AGORA Components
 *
 * Modern React components for the AGORA landing page.
 * All components support ES modules, TypeScript, and responsive design.
 *
 * @module agora-components
 */

// Core components
export { default as FeatureCard } from './FeatureCard.jsx';
export { default as SecurityBadge, SecurityBadgeGrid } from './SecurityBadge.jsx';
export { default as HowItWorks, HowItWorksCompact } from './HowItWorks.jsx';
export { default as CodeDemo } from './CodeDemo.jsx';
export { default as StatsCounter, StatsGrid, AGORA_STATS } from './StatsCounter.jsx';

/**
 * Usage Examples:
 *
 * // Import individual components
 * import { FeatureCard, SecurityBadge, HowItWorks } from './components';
 *
 * // Or import all
 * import * as AgoraComponents from './components';
 *
 * // Use in your React app
 * function App() {
 *   return (
 *     <div>
 *       <FeatureCard
 *         icon="🔐"
 *         title="Ed25519 Auth"
 *         description="Cryptographic signatures, no API keys"
 *         highlight={true}
 *       />
 *
 *       <SecurityBadge
 *         variant="stat"
 *         label="API Keys Stored"
 *         value="0"
 *         positive={true}
 *       />
 *
 *       <HowItWorks />
 *
 *       <CodeDemo title="Quick Start" />
 *
 *       <StatsGrid stats={AGORA_STATS} columns={3} />
 *     </div>
 *   );
 * }
 */
