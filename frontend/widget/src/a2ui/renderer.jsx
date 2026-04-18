import { COMPONENT_REGISTRY } from './registry';

/**
 * Recursively renders an A2UI node tree.
 * Supports both the new `a2ui` node-tree format and the legacy `data_view` format.
 */
export function A2UINodeRenderer({ node, onCommand }) {
  if (!node) return null;

  // Leaf: plain string value
  if (typeof node === 'string') {
    return <span className="a2ui-text a2ui-text-body">{node}</span>;
  }

  // Legacy backward compat: data_view → pass to AdaptiveView (handled in App.jsx)
  if (node.data_view) return null; // Handled by parent

  const componentName = (node.component || '').toLowerCase();
  const Component = COMPONENT_REGISTRY[componentName];

  if (!Component) {
    // Unknown component: render as a labeled text row
    return (
      <div className="a2ui-unknown-node">
        <span className="a2ui-unknown-tag">[{node.component || '?'}]</span>
        {node.value && <span> {node.value}</span>}
      </div>
    );
  }

  // Recursive renderNode function passed to layout/navigation components
  const renderNode = (child, key) => (
    <A2UINodeRenderer key={key} node={child} onCommand={onCommand} />
  );

  return (
    <Component
      {...node}
      renderNode={renderNode}
      onCommand={onCommand}
    />
  );
}

/**
 * Top-level renderer that wraps a parsed A2UI block.
 * Handles the `{ "a2ui": { component: "...", ... } }` envelope.
 */
export function A2UIRenderer({ data, onCommand }) {
  // New node-tree protocol
  if (data.a2ui) {
    return (
      <div className="a2ui-wrapper a2ui-v3">
        <A2UINodeRenderer node={data.a2ui} onCommand={onCommand} />
      </div>
    );
  }

  // Legacy data_view protocol (backward compat)
  if (data.data_view) {
    const { text, layout = 'grid', items = [], actions = [] } = data.data_view;
    return (
      <div className="a2ui-wrapper">
        {text && <p className="a2ui-title">{text}</p>}
        <LegacyAdaptiveView items={items} layout={layout} onCommand={onCommand} />
        {actions.length > 0 && (
          <div className="a2ui-actions">
            {actions.map((action, idx) => (
              <button
                key={idx}
                className={`a2ui-btn ${action.variant || 'primary'}`}
                onClick={() => onCommand(action.message)}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Unknown format fallback
  return <div className="a2ui-unknown">{JSON.stringify(data)}</div>;
}

// ─── Legacy AdaptiveView (data_view format backward compat) ──────────────────
function LegacyAdaptiveView({ items, layout, onCommand }) {
  return (
    <div className={`a2ui-adaptive-view ${layout}`}>
      {items.map((item, i) => (
        <div className="a2ui-card" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
          {Object.entries(item).map(([key, value]) => {
            if (value === null || value === undefined) return null;
            const lowerKey = key.toLowerCase();

            if (lowerKey === 'status' || lowerKey === 'state') {
              return (
                <div key={key} className={`a2ui-status-badge ${String(value).toLowerCase()}`}>
                  {String(value)}
                </div>
              );
            }

            const isLevel = lowerKey === 'level' || lowerKey === 'proficiency';
            if (isLevel) {
              const sanitize = (val) => {
                if (typeof val === 'number') return val;
                const num = parseInt(String(val).match(/\d+/)?.[0]);
                if (!isNaN(num)) return num;
                const map = { expert: 95, advanced: 85, intermediate: 70, beginner: 40, basic: 40 };
                return map[String(val).toLowerCase()] || 0;
              };
              const numericValue = sanitize(value);
              return (
                <div className="card-metric" key={key}>
                  <div className="metric-bar-track">
                    <div className="metric-bar-fill" style={{ '--target': `${numericValue}%` }} />
                  </div>
                  <span className="metric-val">{value}</span>
                </div>
              );
            }

            if (typeof value === 'boolean' || lowerKey === 'selected') {
              return (
                <div className="card-row checkbox" key={key}>
                  <input type="checkbox" checked={!!value} readOnly />
                  <span className="row-key">{key}</span>
                </div>
              );
            }

            return (
              <div className="card-row" key={key}>
                <span className="row-key">{key}</span>
                <span className="row-value">{String(value)}</span>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
