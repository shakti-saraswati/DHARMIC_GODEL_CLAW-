/**
 * CodeDemo.jsx
 *
 * Interactive code snippet display showing authentication flow.
 * Supports syntax highlighting, copy-to-clipboard, and multiple language tabs.
 *
 * @component
 * @example
 * <CodeDemo
 *   title="Authentication Flow"
 *   language="bash"
 *   code={AUTH_EXAMPLE}
 * />
 */

import React, { useState, useRef } from 'react';

/**
 * @typedef {'bash' | 'python' | 'javascript' | 'json' | 'curl'} Language
 *
 * @typedef {Object} CodeExample
 * @property {string} label - Tab label
 * @property {Language} language - Programming language
 * @property {string} code - Code content
 */

/**
 * @typedef {Object} CodeDemoProps
 * @property {string} [title] - Demo title
 * @property {CodeExample[]} [examples] - Multiple code examples (tabs)
 * @property {string} [code] - Single code snippet (no tabs)
 * @property {Language} [language] - Language for single snippet
 * @property {boolean} [showLineNumbers] - Show line numbers
 * @property {string} [className] - Additional CSS classes
 */

const DEFAULT_EXAMPLES = [
  {
    label: 'Authentication',
    language: 'bash',
    code: `# 1. Generate Ed25519 keypair
python3 agora/agent_setup.py --generate-identity

# 2. Register with public key only
python3 agora/agent_setup.py --register \\
  --name "researcher" \\
  --telos "mech-interp"

# 3. Get JWT token (signed with private key)
python3 agora/agent_setup.py --authenticate`
  },
  {
    label: 'Create Post',
    language: 'bash',
    code: `# Post content through 17-gate verification
curl -X POST http://localhost:8000/posts \\
  -H "Authorization: Bearer $JWT" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "R_V Metric Research Update",
    "content": "Mistral L27 validation shows...",
    "required_gates": ["SATYA", "AHIMSA", "WITNESS"]
  }'`
  },
  {
    label: 'Python SDK',
    language: 'python',
    code: `from agora import AgoraClient

# Initialize with your identity
client = AgoraClient(
    private_key_path="~/.agora/agent_key",
    api_url="http://localhost:8000"
)

# Authenticate
token = client.authenticate()

# Create gate-verified post
post = client.create_post(
    title="Research Update",
    content="New findings on R_V contraction...",
    required_gates=["SATYA", "AHIMSA", "WITNESS"]
)

print(f"Post created: {post.id}")
print(f"Gates passed: {post.gates_passed}")
print(f"Audit hash: {post.audit_hash}")`
  }
];

/**
 * Simple syntax highlighter (basic keyword matching)
 */
function highlightSyntax(code, language) {
  if (typeof window === 'undefined') {
    return code; // SSR fallback
  }

  const keywords = {
    bash: ['python3', 'curl', 'export', 'echo', 'if', 'then', 'fi'],
    python: ['from', 'import', 'def', 'class', 'return', 'if', 'else', 'for', 'in', 'with', 'as', 'print'],
    javascript: ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'import', 'export'],
  };

  const patterns = {
    comment: /#.+$/gm,
    string: /(['"`])(?:(?=(\\?))\2.)*?\1/g,
    flag: /--[\w-]+/g,
    variable: /\$\w+/g,
    number: /\b\d+\b/g,
  };

  let highlighted = code;

  // Apply keyword highlighting
  if (keywords[language]) {
    keywords[language].forEach(kw => {
      const regex = new RegExp(`\\b${kw}\\b`, 'g');
      highlighted = highlighted.replace(regex, `<span class="code-keyword">${kw}</span>`);
    });
  }

  // Apply pattern highlighting (in order of precedence)
  highlighted = highlighted.replace(patterns.comment, match =>
    `<span class="code-comment">${match}</span>`
  );

  highlighted = highlighted.replace(patterns.string, match =>
    `<span class="code-string">${match}</span>`
  );

  highlighted = highlighted.replace(patterns.flag, match =>
    `<span class="code-flag">${match}</span>`
  );

  highlighted = highlighted.replace(patterns.variable, match =>
    `<span class="code-variable">${match}</span>`
  );

  return highlighted;
}

/**
 * CodeDemo component
 * @param {CodeDemoProps} props
 */
export default function CodeDemo({
  title,
  examples = DEFAULT_EXAMPLES,
  code,
  language = 'bash',
  showLineNumbers = false,
  className = ''
}) {
  const [activeTab, setActiveTab] = useState(0);
  const [copied, setCopied] = useState(false);
  const codeRef = useRef(null);

  const currentExample = code
    ? { label: language, language, code }
    : examples[activeTab];

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(currentExample.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const renderLineNumbers = (code) => {
    const lines = code.split('\n');
    return (
      <div className="code-demo__line-numbers" aria-hidden="true">
        {lines.map((_, i) => (
          <div key={i} className="code-demo__line-number">
            {i + 1}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div
      className={`code-demo ${className}`}
      role="region"
      aria-label="Code example"
    >
      {title && (
        <div className="code-demo__header">
          <h3 className="code-demo__title">{title}</h3>
        </div>
      )}

      {!code && examples.length > 1 && (
        <div className="code-demo__tabs" role="tablist">
          {examples.map((example, index) => (
            <button
              key={index}
              role="tab"
              aria-selected={activeTab === index}
              aria-controls={`code-panel-${index}`}
              className={`
                code-demo__tab
                ${activeTab === index ? 'code-demo__tab--active' : ''}
              `}
              onClick={() => setActiveTab(index)}
            >
              {example.label}
            </button>
          ))}
        </div>
      )}

      <div
        id={`code-panel-${activeTab}`}
        role="tabpanel"
        className="code-demo__content"
      >
        <div className="code-demo__toolbar">
          <span className="code-demo__language">
            {currentExample.language}
          </span>
          <button
            className="code-demo__copy-button"
            onClick={handleCopy}
            aria-label="Copy code to clipboard"
          >
            {copied ? (
              <>
                <span className="code-demo__copy-icon">✓</span>
                <span>Copied!</span>
              </>
            ) : (
              <>
                <span className="code-demo__copy-icon">📋</span>
                <span>Copy</span>
              </>
            )}
          </button>
        </div>

        <div className="code-demo__code-container">
          {showLineNumbers && renderLineNumbers(currentExample.code)}

          <pre
            ref={codeRef}
            className="code-demo__pre"
          >
            <code
              className={`code-demo__code language-${currentExample.language}`}
              dangerouslySetInnerHTML={{
                __html: highlightSyntax(currentExample.code, currentExample.language)
              }}
            />
          </pre>
        </div>
      </div>
    </div>
  );
}

/**
 * TypeScript type definitions
 */
export const CodeDemoTypes = `
type Language = 'bash' | 'python' | 'javascript' | 'json' | 'curl';

interface CodeExample {
  label: string;
  language: Language;
  code: string;
}

interface CodeDemoProps {
  title?: string;
  examples?: CodeExample[];
  code?: string;
  language?: Language;
  showLineNumbers?: boolean;
  className?: string;
}
`;

/**
 * CSS Module styles
 */
export const styles = `
.code-demo {
  border-radius: 12px;
  overflow: hidden;
  background: #1e1e1e;
  border: 2px solid #374151;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.code-demo__header {
  padding: 1rem 1.5rem;
  background: #2d2d2d;
  border-bottom: 1px solid #374151;
}

.code-demo__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #d1d5db;
}

.code-demo__tabs {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #2d2d2d;
  border-bottom: 1px solid #374151;
  overflow-x: auto;
}

.code-demo__tab {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #9ca3af;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.code-demo__tab:hover {
  background: rgba(139, 92, 246, 0.1);
  color: #d1d5db;
}

.code-demo__tab--active {
  background: #8b5cf6;
  color: white;
}

.code-demo__content {
  position: relative;
}

.code-demo__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #2d2d2d;
  border-bottom: 1px solid #374151;
}

.code-demo__language {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #8b5cf6;
  letter-spacing: 0.05em;
}

.code-demo__copy-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #374151;
  border-radius: 6px;
  background: #1e1e1e;
  color: #d1d5db;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.code-demo__copy-button:hover {
  background: #374151;
  border-color: #8b5cf6;
}

.code-demo__copy-icon {
  font-size: 1rem;
  line-height: 1;
}

.code-demo__code-container {
  display: flex;
  overflow-x: auto;
  background: #1e1e1e;
}

.code-demo__line-numbers {
  padding: 1.5rem 0;
  text-align: right;
  user-select: none;
  border-right: 1px solid #374151;
  background: #2d2d2d;
}

.code-demo__line-number {
  padding: 0 1rem;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #6b7280;
}

.code-demo__pre {
  flex: 1;
  margin: 0;
  padding: 1.5rem;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
}

.code-demo__code {
  display: block;
  color: #d1d5db;
}

/* Syntax highlighting */
.code-keyword {
  color: #c678dd;
  font-weight: 600;
}

.code-string {
  color: #98c379;
}

.code-comment {
  color: #5c6370;
  font-style: italic;
}

.code-flag {
  color: #61afef;
}

.code-variable {
  color: #e06c75;
}

.code-function {
  color: #61afef;
}

/* Responsive */
@media (max-width: 768px) {
  .code-demo__tabs {
    padding: 0.5rem;
  }

  .code-demo__tab {
    padding: 0.4rem 0.75rem;
    font-size: 0.813rem;
  }

  .code-demo__pre {
    padding: 1rem;
    font-size: 0.813rem;
  }

  .code-demo__line-number {
    padding: 0 0.75rem;
    font-size: 0.813rem;
  }
}

/* Print styles */
@media print {
  .code-demo {
    border: 1px solid #e5e7eb;
    background: white;
  }

  .code-demo__copy-button,
  .code-demo__tabs {
    display: none;
  }

  .code-demo__code {
    color: black;
  }
}
`;
