#!/bin/bash

#####################################################################
# DHARMIC_AGORA Accessibility Validation Script
# 
# Runs automated accessibility checks and generates report
# Requires: axe-cli, lighthouse-cli, pa11y
#####################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
URL="${1:-http://localhost:8000/explorer}"
OUTPUT_DIR="evidence/accessibility_$(date +%Y%m%d_%H%M%S)"
REQUIRED_SCORE=90

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       DHARMIC_AGORA Accessibility Validation              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if tools are installed
echo -e "${YELLOW}Checking required tools...${NC}"

TOOLS_MISSING=0

if ! command -v axe &> /dev/null; then
    echo -e "${RED}✗ axe-cli not found${NC}"
    echo "  Install: npm install -g axe-cli"
    TOOLS_MISSING=1
fi

if ! command -v lighthouse &> /dev/null; then
    echo -e "${RED}✗ lighthouse not found${NC}"
    echo "  Install: npm install -g lighthouse"
    TOOLS_MISSING=1
fi

if ! command -v pa11y &> /dev/null; then
    echo -e "${RED}✗ pa11y not found${NC}"
    echo "  Install: npm install -g pa11y"
    TOOLS_MISSING=1
fi

if [ $TOOLS_MISSING -eq 1 ]; then
    echo ""
    echo -e "${RED}Missing required tools. Please install them first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All tools installed${NC}"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo -e "${BLUE}Output directory: $OUTPUT_DIR${NC}"
echo ""

# Check if server is running
echo -e "${YELLOW}Checking if server is accessible...${NC}"
if ! curl -s --head "$URL" | grep "200 OK" > /dev/null; then
    echo -e "${RED}✗ Server not accessible at $URL${NC}"
    echo "  Please start the server first: python3 -m agora"
    exit 1
fi
echo -e "${GREEN}✓ Server is accessible${NC}"
echo ""

#####################################################################
# AXE SCAN
#####################################################################

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Running Axe Accessibility Scan...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

axe "$URL" \
    --tags wcag2a,wcag2aa,wcag21a,wcag21aa \
    --save "$OUTPUT_DIR/axe-report.json" \
    --dir "$OUTPUT_DIR" \
    || AXE_EXIT=$?

if [ -f "$OUTPUT_DIR/axe-report.json" ]; then
    # Parse results
    VIOLATIONS=$(jq '.violations | length' "$OUTPUT_DIR/axe-report.json")
    PASSES=$(jq '.passes | length' "$OUTPUT_DIR/axe-report.json")
    
    echo ""
    echo -e "Results:"
    echo -e "  ${RED}Violations: $VIOLATIONS${NC}"
    echo -e "  ${GREEN}Passes: $PASSES${NC}"
    
    if [ "$VIOLATIONS" -eq 0 ]; then
        echo -e "${GREEN}✓ No violations found!${NC}"
    else
        echo -e "${RED}✗ Violations detected${NC}"
        echo ""
        echo "Top violations:"
        jq -r '.violations[] | "  - \(.id): \(.nodes | length) instances"' "$OUTPUT_DIR/axe-report.json" | head -5
    fi
else
    echo -e "${RED}✗ Axe scan failed${NC}"
fi

echo ""

#####################################################################
# LIGHTHOUSE SCAN
#####################################################################

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Running Lighthouse Accessibility Audit...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

lighthouse "$URL" \
    --only-categories=accessibility \
    --output=json \
    --output=html \
    --output-path="$OUTPUT_DIR/lighthouse-report" \
    --chrome-flags="--headless" \
    --quiet \
    || LIGHTHOUSE_EXIT=$?

if [ -f "$OUTPUT_DIR/lighthouse-report.report.json" ]; then
    SCORE=$(jq -r '.categories.accessibility.score * 100' "$OUTPUT_DIR/lighthouse-report.report.json")
    
    echo ""
    echo -e "Accessibility Score: ${BLUE}$SCORE/100${NC}"
    
    if (( $(echo "$SCORE >= $REQUIRED_SCORE" | bc -l) )); then
        echo -e "${GREEN}✓ Score meets requirement (≥$REQUIRED_SCORE)${NC}"
    else
        echo -e "${RED}✗ Score below requirement (≥$REQUIRED_SCORE)${NC}"
    fi
    
    echo ""
    echo "Failed audits:"
    jq -r '.categories.accessibility.auditRefs[] | select(.group != null) | .id' "$OUTPUT_DIR/lighthouse-report.report.json" | while read audit; do
        RESULT=$(jq -r ".audits[\"$audit\"].score" "$OUTPUT_DIR/lighthouse-report.report.json")
        if [ "$RESULT" = "null" ] || [ "$RESULT" = "0" ]; then
            TITLE=$(jq -r ".audits[\"$audit\"].title" "$OUTPUT_DIR/lighthouse-report.report.json")
            echo -e "  ${RED}✗${NC} $TITLE"
        fi
    done
else
    echo -e "${RED}✗ Lighthouse scan failed${NC}"
fi

echo ""

#####################################################################
# PA11Y SCAN
#####################################################################

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Running Pa11y Accessibility Test...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

pa11y "$URL" \
    --standard WCAG2AA \
    --reporter json \
    > "$OUTPUT_DIR/pa11y-report.json" \
    || PA11Y_EXIT=$?

if [ -f "$OUTPUT_DIR/pa11y-report.json" ]; then
    ERRORS=$(jq '[.[] | select(.type == "error")] | length' "$OUTPUT_DIR/pa11y-report.json")
    WARNINGS=$(jq '[.[] | select(.type == "warning")] | length' "$OUTPUT_DIR/pa11y-report.json")
    NOTICES=$(jq '[.[] | select(.type == "notice")] | length' "$OUTPUT_DIR/pa11y-report.json")
    
    echo ""
    echo -e "Results:"
    echo -e "  ${RED}Errors: $ERRORS${NC}"
    echo -e "  ${YELLOW}Warnings: $WARNINGS${NC}"
    echo -e "  ${BLUE}Notices: $NOTICES${NC}"
    
    if [ "$ERRORS" -eq 0 ]; then
        echo -e "${GREEN}✓ No errors found!${NC}"
    else
        echo -e "${RED}✗ Errors detected${NC}"
        echo ""
        echo "Top errors:"
        jq -r '[.[] | select(.type == "error")] | .[0:3] | .[] | "  - \(.message)"' "$OUTPUT_DIR/pa11y-report.json"
    fi
else
    echo -e "${RED}✗ Pa11y scan failed${NC}"
fi

echo ""

#####################################################################
# GENERATE SUMMARY REPORT
#####################################################################

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Generating Summary Report...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

cat > "$OUTPUT_DIR/SUMMARY.md" << SUMMARY
# DHARMIC_AGORA Accessibility Validation Report

**Date:** $(date)
**URL:** $URL
**Output Directory:** $OUTPUT_DIR

---

## Summary

### Axe Scan
- **Violations:** $VIOLATIONS
- **Passes:** $PASSES
- **Status:** $([ "$VIOLATIONS" -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")

### Lighthouse Audit
- **Accessibility Score:** $SCORE/100
- **Required Score:** $REQUIRED_SCORE
- **Status:** $([ $(echo "$SCORE >= $REQUIRED_SCORE" | bc -l) -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL")

### Pa11y Test
- **Errors:** $ERRORS
- **Warnings:** $WARNINGS
- **Notices:** $NOTICES
- **Status:** $([ "$ERRORS" -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")

---

## Overall Status

$(
if [ "$VIOLATIONS" -eq 0 ] && [ "$ERRORS" -eq 0 ] && [ $(echo "$SCORE >= $REQUIRED_SCORE" | bc -l) -eq 1 ]; then
    echo "### ✅ ALL CHECKS PASSED"
    echo ""
    echo "The site meets WCAG 2.1 Level AA accessibility standards."
else
    echo "### ❌ ACCESSIBILITY ISSUES DETECTED"
    echo ""
    echo "The site has accessibility issues that need to be addressed."
    echo ""
    echo "**Action Required:**"
    echo "1. Review detailed reports in this directory"
    echo "2. Implement fixes according to ACCESSIBILITY_CHECKLIST.md"
    echo "3. Re-run validation"
fi
)

---

## Detailed Reports

- **Axe Report:** [axe-report.json](axe-report.json)
- **Lighthouse Report:** [lighthouse-report.report.html](lighthouse-report.report.html)
- **Pa11y Report:** [pa11y-report.json](pa11y-report.json)

---

## Next Steps

1. Review all detected issues
2. Prioritize critical and high-severity issues
3. Implement fixes according to [ACCESSIBILITY_CHECKLIST.md](../ACCESSIBILITY_CHECKLIST.md)
4. Verify fixes with manual testing
5. Re-run this validation script

---

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)

---

*Generated by DHARMIC_AGORA accessibility validation script*
SUMMARY

echo -e "${GREEN}✓ Summary report generated${NC}"
echo ""

#####################################################################
# FINAL OUTPUT
#####################################################################

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Validation Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Overall status
OVERALL_PASS=1

if [ "$VIOLATIONS" -ne 0 ] || [ "$ERRORS" -ne 0 ]; then
    OVERALL_PASS=0
fi

if [ $(echo "$SCORE < $REQUIRED_SCORE" | bc -l) -eq 1 ]; then
    OVERALL_PASS=0
fi

if [ $OVERALL_PASS -eq 1 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   ✅ ALL CHECKS PASSED                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              ❌ ACCESSIBILITY ISSUES DETECTED              ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
fi

echo ""
echo -e "Full report: ${BLUE}$OUTPUT_DIR/SUMMARY.md${NC}"
echo -e "View Lighthouse report: ${BLUE}open $OUTPUT_DIR/lighthouse-report.report.html${NC}"
echo ""

exit $([ $OVERALL_PASS -eq 1 ] && echo 0 || echo 1)
