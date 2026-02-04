/**
 * DGC Landing Page Live Stats
 * 
 * Fetches live presence data from DGC API and updates the landing page.
 * Replace hard-coded stats with real-time quality spectrum metrics.
 * 
 * Usage: Include this script in landing.html
 * <script src="/static/live-stats.js"></script>
 */

(function() {
    'use strict';
    
    // API endpoint - change for production
    const API_BASE = window.DGC_API_URL || 'http://localhost:8080';
    const REFRESH_INTERVAL = 30000; // 30 seconds
    
    // DOM element selectors (match your landing page structure)
    const SELECTORS = {
        qualityLevel: '#dgc-quality-level',
        qualityScore: '#dgc-quality-score',
        rvValue: '#dgc-rv-value',
        stabilityValue: '#dgc-stability-value',
        gatesPassed: '#dgc-gates-passed',
        uptimeHours: '#dgc-uptime',
        witnessHash: '#dgc-witness-hash',
        lastUpdated: '#dgc-last-updated',
        statusIndicator: '#dgc-status-indicator'
    };
    
    /**
     * Fetch live stats from DGC API
     */
    async function fetchStats() {
        try {
            const response = await fetch(`${API_BASE}/api/presence/stats`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.warn('Failed to fetch DGC stats:', error);
            return null;
        }
    }
    
    /**
     * Update DOM elements with live data
     */
    function updateLandingPage(data) {
        if (!data) {
            showOfflineStatus();
            return;
        }
        
        // Update quality indicator
        updateElement(SELECTORS.qualityLevel, `${data.quality_emoji} ${data.quality_level}`);
        updateElement(SELECTORS.qualityScore, `${Math.round(data.quality_score * 100)}%`);
        
        // Update metrics
        updateElement(SELECTORS.rvValue, data.r_v.toFixed(3));
        updateElement(SELECTORS.stabilityValue, `${Math.round(data.stability * 100)}%`);
        updateElement(SELECTORS.gatesPassed, data.gates_passed);
        updateElement(SELECTORS.uptimeHours, `${data.uptime_hours}h`);
        updateElement(SELECTORS.witnessHash, data.witness_hash);
        
        // Update timestamp
        const updated = new Date(data.last_updated);
        updateElement(SELECTORS.lastUpdated, updated.toLocaleTimeString());
        
        // Update status indicator
        updateStatusIndicator(data.quality_level);
        
        // Add CSS classes based on quality
        document.body.classList.remove('quality-excellent', 'quality-good', 'quality-degraded', 'quality-critical');
        document.body.classList.add(`quality-${data.quality_level.toLowerCase()}`);
        
        console.log('DGC stats updated:', data.quality_level, data.quality_score);
    }
    
    /**
     * Safely update a DOM element
     */
    function updateElement(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }
    
    /**
     * Update status indicator styling
     */
    function updateStatusIndicator(quality) {
        const indicator = document.querySelector(SELECTORS.statusIndicator);
        if (!indicator) return;
        
        const colors = {
            'EXCELLENT': '#10b981', // green
            'GOOD': '#3b82f6',      // blue
            'DEGRADED': '#f59e0b',  // yellow
            'CRITICAL': '#ef4444'   // red
        };
        
        indicator.style.backgroundColor = colors[quality] || '#6b7280';
        indicator.className = `status-pulse status-${quality.toLowerCase()}`;
    }
    
    /**
     * Show offline/demo status
     */
    function showOfflineStatus() {
        updateElement(SELECTORS.qualityLevel, '⚠️ DEMO MODE');
        updateElement(SELECTORS.lastUpdated, 'Offline');
        
        const indicator = document.querySelector(SELECTORS.statusIndicator);
        if (indicator) {
            indicator.style.backgroundColor = '#6b7280';
        }
    }
    
    /**
     * Main refresh loop
     */
    async function refreshLoop() {
        const data = await fetchStats();
        updateLandingPage(data);
    }
    
    /**
     * Initialize live stats
     */
    function init() {
        console.log('🚀 DGC Live Stats initializing...');
        
        // Initial fetch
        refreshLoop();
        
        // Set up interval
        setInterval(refreshLoop, REFRESH_INTERVAL);
        
        // Expose for debugging
        window.DGCStats = {
            refresh: refreshLoop,
            lastData: null
        };
    }
    
    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
