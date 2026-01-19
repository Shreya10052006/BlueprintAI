/**
 * Modern UI Flowchart Renderer
 * =============================
 * Replaces Mermaid with HTML cards + SVG arrows
 * Renders from structured JSON data
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

const FLOWCHART_CONFIG = {
    cardWidth: 160,
    cardHeight: 90,
    horizontalGap: 100,
    verticalGap: 80,
    arrowColor: '#4F7CFF',
    arrowWidth: 2,
    maxColumns: 4
};

const TAG_COLORS = {
    'NEW': { bg: '#dcfce7', color: '#166534' },
    'DONE': { bg: '#dbeafe', color: '#1e40af' },
    'IN PROGRESS': { bg: '#fef3c7', color: '#92400e' },
    'ATTENTION': { bg: '#fee2e2', color: '#991b1b' },
    'REVIEW': { bg: '#f3e8ff', color: '#6b21a8' },
    'PRIORITY': { bg: '#ffedd5', color: '#c2410c' }
};

const TYPE_ICONS = {
    'frontend': '🖥️',
    'backend': '⚙️',
    'database': '🗄️',
    'external': '🌐',
    'auth': '🔐',
    'storage': '📦',
    'api': '🔌'
};

// =============================================================================
// DEFAULT DIAGRAMS (FALLBACK)
// =============================================================================

function getDefaultUserFlowDiagram() {
    // Multi-branch structure like reference images
    return {
        nodes: [
            // Level 0 - Entry
            { id: 'login', label: 'Login / Register', tags: ['NEW', 'DONE'] },

            // Level 1 - Main navigation (multiple nodes at same level)
            { id: 'home', label: 'Home / Dashboard', tags: ['ASAP', 'ATTENTION'] },
            { id: 'profile', label: 'User Profile', tags: ['NEW', 'REVIEW'] },

            // Level 2 - Core features (branching)
            { id: 'feature1', label: 'Core Feature', tags: ['IN PROGRESS'] },
            { id: 'feature2', label: 'Browse / Search', tags: ['ATTENTION'] },
            { id: 'settings', label: 'Settings', tags: ['REVIEW'] },

            // Level 3 - Actions/Tasks
            { id: 'action', label: 'Take Action', tags: ['IN PROGRESS', 'ATTENTION'] },

            // Level 4 - Outcomes (multiple at same level)
            { id: 'success', label: 'Success', tags: ['NEW', 'PRIORITY'] },
            { id: 'failure', label: 'Retry / Error', tags: ['DONE', 'REVIEW'] }
        ],
        edges: [
            // Entry to main nav
            ['login', 'home'],
            ['login', 'profile'],

            // Home to features (branching)
            ['home', 'feature1'],
            ['home', 'feature2'],

            // Profile to settings
            ['profile', 'settings'],

            // Features to action
            ['feature1', 'action'],
            ['feature2', 'action'],

            // Action to outcomes (branching)
            ['action', 'success'],
            ['action', 'failure'],

            // Failure loops back
            ['failure', 'home']
        ]
    };
}

function getDefaultTechStackDiagram() {
    return {
        nodes: [
            { id: 'frontend', label: 'Frontend UI', type: 'frontend' },
            { id: 'backend', label: 'Backend API', type: 'backend' },
            { id: 'database', label: 'Database', type: 'database' },
            { id: 'external', label: 'External APIs', type: 'external' }
        ],
        edges: [
            ['frontend', 'backend'],
            ['backend', 'database'],
            ['backend', 'external']
        ]
    };
}

// =============================================================================
// LAYOUT ALGORITHM - LEVEL-WISE (NOT CHAIN-WISE)
// =============================================================================

/**
 * Calculates node positions using semantic level grouping.
 * Level = shortest distance from root
 * Multiple nodes at same level share X coordinate
 * Branches go DOWN (Y-axis), main flow goes RIGHT (X-axis)
 */
function calculateNodePositions(nodes, edges) {
    if (!nodes || nodes.length === 0) return {};

    const positions = {};
    const nodeLevels = {}; // nodeId -> level number
    const levels = {};     // level number -> [nodeIds]

    // Build adjacency lists
    const adjacency = {};
    const reverseAdj = {}; // for finding parents
    nodes.forEach(n => {
        adjacency[n.id] = [];
        reverseAdj[n.id] = [];
    });
    edges.forEach(([from, to]) => {
        if (adjacency[from]) adjacency[from].push(to);
        if (reverseAdj[to]) reverseAdj[to].push(from);
    });

    // Find root nodes (no incoming edges)
    const hasIncoming = new Set(edges.map(e => e[1]));
    let roots = nodes.filter(n => !hasIncoming.has(n.id));
    if (roots.length === 0) roots = [nodes[0]];

    // BFS to assign levels - shortest path from any root
    const queue = roots.map(n => ({ id: n.id, level: 0 }));
    const visited = new Set();

    while (queue.length > 0) {
        const { id, level } = queue.shift();
        if (!id || visited.has(id)) continue;

        // Record level (first visit = shortest path)
        visited.add(id);
        nodeLevels[id] = level;

        // Add children to queue
        (adjacency[id] || []).forEach(childId => {
            if (!visited.has(childId)) {
                queue.push({ id: childId, level: level + 1 });
            }
        });
    }

    // Add any unvisited nodes to last level + 1
    nodes.forEach(n => {
        if (!visited.has(n.id)) {
            const maxLevel = Math.max(...Object.values(nodeLevels), 0);
            nodeLevels[n.id] = maxLevel + 1;
        }
    });

    // Group nodes by level
    nodes.forEach(n => {
        const level = nodeLevels[n.id] || 0;
        if (!levels[level]) levels[level] = [];
        levels[level].push(n.id);
    });

    // COMPACT LAYOUT: Limit horizontal spread
    const config = FLOWCHART_CONFIG;
    const maxLevels = Object.keys(levels).length;

    // Calculate positions - level determines X, index in level determines Y
    const levelNumbers = Object.keys(levels).map(Number).sort((a, b) => a - b);

    levelNumbers.forEach(levelNum => {
        const nodeIds = levels[levelNum];
        const nodeCount = nodeIds.length;

        // X position: all nodes at same level share X
        const x = 30 + levelNum * (config.cardWidth + config.horizontalGap);

        // Y positions: distribute vertically, centered
        const totalHeight = nodeCount * config.cardHeight + (nodeCount - 1) * config.verticalGap;
        const startY = Math.max(30, (300 - totalHeight) / 2);

        nodeIds.forEach((id, idx) => {
            positions[id] = {
                x: x,
                y: startY + idx * (config.cardHeight + config.verticalGap)
            };
        });
    });

    // Normalize positions (ensure all positive)
    let minX = Infinity, minY = Infinity;
    Object.values(positions).forEach(p => {
        if (p.x < minX) minX = p.x;
        if (p.y < minY) minY = p.y;
    });

    const offsetX = minX < 20 ? 20 - minX : 0;
    const offsetY = minY < 20 ? 20 - minY : 0;

    Object.values(positions).forEach(p => {
        p.x += offsetX;
        p.y += offsetY;
    });

    return positions;
}

// =============================================================================
// CARD RENDERER
// =============================================================================

function createFlowCard(node, position) {
    const config = FLOWCHART_CONFIG;

    const card = document.createElement('div');
    card.className = 'flow-card';
    card.id = `flow-card-${node.id}`;
    card.style.cssText = `
        left: ${position.x}px;
        top: ${position.y}px;
        width: ${config.cardWidth}px;
        min-height: ${config.cardHeight}px;
    `;

    // Icon for tech stack nodes
    const icon = node.type && TYPE_ICONS[node.type] ? `<span class="flow-card-icon">${TYPE_ICONS[node.type]}</span>` : '';

    // Title
    const title = document.createElement('div');
    title.className = 'flow-card-title';
    title.innerHTML = `${icon}${escapeHtmlFlowchart(node.label)}`;
    card.appendChild(title);

    // Tags
    if (node.tags && node.tags.length > 0) {
        const tagsContainer = document.createElement('div');
        tagsContainer.className = 'flow-card-tags';

        node.tags.forEach(tag => {
            const tagEl = document.createElement('span');
            tagEl.className = 'flow-tag';
            const colors = TAG_COLORS[tag.toUpperCase()] || { bg: '#f1f5f9', color: '#475569' };
            tagEl.style.cssText = `background: ${colors.bg}; color: ${colors.color};`;
            tagEl.textContent = tag;
            tagsContainer.appendChild(tagEl);
        });

        card.appendChild(tagsContainer);
    }

    // Type badge for tech stack
    if (node.type && !node.tags) {
        const typeBadge = document.createElement('div');
        typeBadge.className = 'flow-card-type';
        typeBadge.textContent = node.type.charAt(0).toUpperCase() + node.type.slice(1);
        card.appendChild(typeBadge);
    }

    return card;
}

function escapeHtmlFlowchart(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// =============================================================================
// ARROW RENDERER (SVG) - PORT-BASED ROUTING
// =============================================================================

function createArrowsSVG(edges, positions, containerWidth, containerHeight) {
    const config = FLOWCHART_CONFIG;
    const ns = 'http://www.w3.org/2000/svg';

    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'flowchart-arrows');
    svg.setAttribute('width', containerWidth);
    svg.setAttribute('height', containerHeight);
    svg.style.cssText = 'position: absolute; top: 0; left: 0; pointer-events: none;';

    // Arrow marker definition
    const defs = document.createElementNS(ns, 'defs');
    const marker = document.createElementNS(ns, 'marker');
    marker.setAttribute('id', 'arrowhead');
    marker.setAttribute('markerWidth', '10');
    marker.setAttribute('markerHeight', '7');
    marker.setAttribute('refX', '9');
    marker.setAttribute('refY', '3.5');
    marker.setAttribute('orient', 'auto');

    const polygon = document.createElementNS(ns, 'polygon');
    polygon.setAttribute('points', '0 0, 10 3.5, 0 7');
    polygon.setAttribute('fill', config.arrowColor);
    marker.appendChild(polygon);
    defs.appendChild(marker);
    svg.appendChild(defs);

    // RULE 1: Calculate outgoing and incoming edge counts per node
    const outgoingEdges = {}; // nodeId -> [toId1, toId2, ...]
    const incomingEdges = {}; // nodeId -> [fromId1, fromId2, ...]

    edges.forEach(([fromId, toId]) => {
        if (!outgoingEdges[fromId]) outgoingEdges[fromId] = [];
        if (!incomingEdges[toId]) incomingEdges[toId] = [];
        outgoingEdges[fromId].push(toId);
        incomingEdges[toId].push(fromId);
    });

    // RULE 2: Calculate port positions for each node
    const outgoingPorts = {}; // nodeId -> { toId: portY }
    const incomingPorts = {}; // nodeId -> { fromId: portY }

    Object.entries(outgoingEdges).forEach(([nodeId, targets]) => {
        const pos = positions[nodeId];
        if (!pos) return;

        const n = targets.length;
        const portSpacing = config.cardHeight / (n + 1);

        outgoingPorts[nodeId] = {};
        targets.forEach((targetId, i) => {
            outgoingPorts[nodeId][targetId] = pos.y + portSpacing * (i + 1);
        });
    });

    Object.entries(incomingEdges).forEach(([nodeId, sources]) => {
        const pos = positions[nodeId];
        if (!pos) return;

        const n = sources.length;
        const portSpacing = config.cardHeight / (n + 1);

        incomingPorts[nodeId] = {};
        sources.forEach((sourceId, i) => {
            incomingPorts[nodeId][sourceId] = pos.y + portSpacing * (i + 1);
        });
    });

    // RULE 3 & 4: Draw arrows with port-based routing
    edges.forEach(([fromId, toId], idx) => {
        const from = positions[fromId];
        const to = positions[toId];
        if (!from || !to) return;

        // Get port Y positions
        const y1 = outgoingPorts[fromId]?.[toId] ?? (from.y + config.cardHeight / 2);
        const y2 = incomingPorts[toId]?.[fromId] ?? (to.y + config.cardHeight / 2);

        // Calculate X positions
        const x1 = from.x + config.cardWidth;
        const x2 = to.x;

        // RULE 3: Calculate curve offset based on horizontal distance
        const horizontalDistance = Math.abs(x2 - x1);
        const curveOffset = Math.max(60, horizontalDistance * 0.4);

        // RULE 4: Add small vertical delta for parallel arrows
        const parallelOffset = ((idx % 3) - 1) * 5; // -5, 0, +5

        // Bezier control points with proper curve separation
        const c1x = x1 + curveOffset;
        const c1y = y1 + parallelOffset;
        const c2x = x2 - curveOffset;
        const c2y = y2 + parallelOffset;

        const path = document.createElementNS(ns, 'path');
        path.setAttribute('d', `M ${x1} ${y1} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${x2} ${y2}`);
        path.setAttribute('stroke', config.arrowColor);
        path.setAttribute('stroke-width', config.arrowWidth);
        path.setAttribute('fill', 'none');
        path.setAttribute('marker-end', 'url(#arrowhead)');

        svg.appendChild(path);
    });

    return svg;
}

// =============================================================================
// MAIN RENDER FUNCTION - TAB-AWARE AUTO-SCALING
// =============================================================================

function renderFlowchart(containerId, diagramData, isUserFlow = true) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Flowchart container not found: ${containerId}`);
        return;
    }

    // Use fallback if no valid data
    let data = diagramData;
    if (!data || !data.nodes || data.nodes.length === 0) {
        data = isUserFlow ? getDefaultUserFlowDiagram() : getDefaultTechStackDiagram();
        console.log(`Using fallback diagram for ${containerId}`);
    }

    // Clear container
    container.innerHTML = '';
    container.className = 'flowchart-container';

    // Calculate positions
    const positions = calculateNodePositions(data.nodes, data.edges || []);
    const config = FLOWCHART_CONFIG;

    // =========================================================================
    // USER FLOW ONLY: Compute TRUE diagram bounds and normalize positions
    // This fixes clipping issues where branching flows exceed container bounds
    // =========================================================================
    if (isUserFlow) {
        // STEP 1: Compute true bounds across ALL nodes
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;

        Object.values(positions).forEach(p => {
            if (p.x < minX) minX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.x + config.cardWidth > maxX) maxX = p.x + config.cardWidth;
            if (p.y + config.cardHeight > maxY) maxY = p.y + config.cardHeight;
        });

        // STEP 2: Normalize positions - shift ALL nodes so minX/minY >= padding
        const PADDING = 30;
        const offsetX = minX < PADDING ? PADDING - minX : 0;
        const offsetY = minY < PADDING ? PADDING - minY : 0;

        if (offsetX > 0 || offsetY > 0) {
            Object.values(positions).forEach(p => {
                p.x += offsetX;
                p.y += offsetY;
            });
            // Update bounds after normalization
            minX += offsetX;
            maxX += offsetX;
            minY += offsetY;
            maxY += offsetY;
        }

        // STEP 3: Calculate container size from normalized bounds
        const diagramWidth = maxX + PADDING;
        const diagramHeight = maxY + PADDING;

        // STEP 4: Get available tab width
        const tabContainer = container.closest('.blueprint-content')
            || container.closest('.tab-content')
            || container.closest('.dashboard-content')
            || container.parentElement;

        const rawWidth = tabContainer ? tabContainer.clientWidth : 0;
        const availableWidth = Math.max(rawWidth - 40, 400); // Minimum 400px fallback

        // STEP 5: Set container to natural diagram size
        container.style.width = `${diagramWidth}px`;
        container.style.height = `${diagramHeight}px`;
        container.style.transformOrigin = 'top left';
        container.style.position = 'relative';
        container.style.overflow = 'visible';

        // STEP 6: Apply scale factor to fit tab width (no horizontal scrolling)
        let scale = 1;
        if (diagramWidth > availableWidth) {
            scale = Math.max(0.3, availableWidth / diagramWidth); // Never go below 0.3
        }

        if (scale < 1) {
            container.style.transform = `scale(${scale})`;
            // Preserve layout height after scaling (negative margin to remove empty space)
            container.style.marginBottom = `${diagramHeight * (scale - 1)}px`;
        } else {
            container.style.transform = 'none';
            container.style.marginBottom = '0';
        }

        // Render arrows first (behind cards)
        const svg = createArrowsSVG(data.edges || [], positions, diagramWidth, diagramHeight);
        container.appendChild(svg);

        // Render cards
        data.nodes.forEach(node => {
            const pos = positions[node.id];
            if (pos) {
                const card = createFlowCard(node, pos);
                container.appendChild(card);
            }
        });

    } else {
        // =========================================================================
        // TECH STACK DIAGRAM: Keep original behavior unchanged
        // =========================================================================
        let maxX = 0, maxY = 0;
        Object.values(positions).forEach(p => {
            if (p.x + config.cardWidth > maxX) maxX = p.x + config.cardWidth;
            if (p.y + config.cardHeight > maxY) maxY = p.y + config.cardHeight;
        });

        const diagramWidth = maxX + 60;
        const diagramHeight = maxY + 60;

        const tabContainer = container.closest('.blueprint-content')
            || container.closest('.tab-content')
            || container.closest('.dashboard-content')
            || container.parentElement;

        const rawWidth = tabContainer ? tabContainer.clientWidth : 0;
        const availableWidth = Math.max(rawWidth - 40, 400);

        container.style.width = `${diagramWidth}px`;
        container.style.height = `${diagramHeight}px`;
        container.style.transformOrigin = 'top left';

        let scale = 1;
        if (diagramWidth > availableWidth) {
            scale = Math.max(0.3, availableWidth / diagramWidth);
        }

        if (scale < 1) {
            container.style.transform = `scale(${scale})`;
            container.style.marginBottom = `${(diagramHeight * (scale - 1))}px`;
        } else {
            container.style.transform = 'none';
            container.style.marginBottom = '0';
        }

        const svg = createArrowsSVG(data.edges || [], positions, diagramWidth, diagramHeight);
        container.appendChild(svg);

        data.nodes.forEach(node => {
            const pos = positions[node.id];
            if (pos) {
                const card = createFlowCard(node, pos);
                container.appendChild(card);
            }
        });
    }

    // Add fallback indicator if using default
    if (!diagramData || !diagramData.nodes || diagramData.nodes.length === 0) {
        const indicator = document.createElement('div');
        indicator.className = 'flowchart-fallback-indicator';
        indicator.textContent = 'Showing default architecture';
        container.appendChild(indicator);
    }
}

// =============================================================================
// EXPORT FUNCTIONS
// =============================================================================

function exportFlowchartAsSVG(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Create a standalone SVG from the flowchart
    const ns = 'http://www.w3.org/2000/svg';
    const width = container.offsetWidth;
    const height = container.offsetHeight;

    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('xmlns', ns);

    // Add background
    const bg = document.createElementNS(ns, 'rect');
    bg.setAttribute('width', '100%');
    bg.setAttribute('height', '100%');
    bg.setAttribute('fill', '#f8fafc');
    svg.appendChild(bg);

    // Copy arrows SVG
    const arrowsSvg = container.querySelector('.flowchart-arrows');
    if (arrowsSvg) {
        svg.innerHTML += arrowsSvg.innerHTML;
    }

    // Convert cards to SVG rectangles and text
    container.querySelectorAll('.flow-card').forEach(card => {
        const rect = document.createElementNS(ns, 'rect');
        const x = parseInt(card.style.left);
        const y = parseInt(card.style.top);
        const w = card.offsetWidth;
        const h = card.offsetHeight;

        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', w);
        rect.setAttribute('height', h);
        rect.setAttribute('rx', '12');
        rect.setAttribute('fill', 'white');
        rect.setAttribute('stroke', '#e2e8f0');
        rect.setAttribute('stroke-width', '1');
        svg.appendChild(rect);

        const title = card.querySelector('.flow-card-title');
        if (title) {
            const text = document.createElementNS(ns, 'text');
            text.setAttribute('x', x + w / 2);
            text.setAttribute('y', y + 35);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('font-size', '12');
            text.setAttribute('font-family', 'system-ui, sans-serif');
            text.setAttribute('fill', '#1e293b');
            text.textContent = title.textContent;
            svg.appendChild(text);
        }
    });

    // Download
    const blob = new Blob([svg.outerHTML], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${containerId}_flowchart.svg`;
    a.click();
    URL.revokeObjectURL(url);
}

function exportFlowchartAsPNG(containerId) {
    const container = document.getElementById(containerId);
    if (!container || typeof html2canvas === 'undefined') {
        alert('PNG export requires html2canvas library');
        return;
    }

    // Reset scale for clean export
    const originalTransform = container.style.transform;
    const originalMargin = container.style.marginBottom;
    container.style.transform = 'none';
    container.style.marginBottom = '0';

    html2canvas(container, {
        backgroundColor: '#ffffff',
        scale: 2
    }).then(canvas => {
        // Restore scale
        container.style.transform = originalTransform;
        container.style.marginBottom = originalMargin;

        const url = canvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = url;
        a.download = `${containerId}_flowchart.png`;
        a.click();
    });
}

/**
 * Export flowchart as PDF (replaces SVG export)
 */
function exportFlowchartAsPDF(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (typeof html2canvas === 'undefined' || typeof jspdf === 'undefined') {
        alert('PDF export requires jsPDF and html2canvas libraries');
        return;
    }

    // Reset scale for clean export
    const originalTransform = container.style.transform;
    const originalMargin = container.style.marginBottom;
    container.style.transform = 'none';
    container.style.marginBottom = '0';

    html2canvas(container, {
        backgroundColor: '#ffffff',
        scale: 2
    }).then(canvas => {
        // Restore scale
        container.style.transform = originalTransform;
        container.style.marginBottom = originalMargin;

        const { jsPDF } = jspdf;
        const imgData = canvas.toDataURL('image/png');
        const imgWidth = canvas.width;
        const imgHeight = canvas.height;

        // Calculate PDF dimensions (fit to page width)
        const pdfWidth = 210; // A4 width in mm
        const pdfHeight = 297; // A4 height in mm
        const margin = 10;
        const contentWidth = pdfWidth - (margin * 2);
        const scaledHeight = (imgHeight * contentWidth) / imgWidth;

        // Create PDF with appropriate orientation
        const orientation = scaledHeight > pdfHeight - (margin * 2) ? 'p' : 'l';
        const pdf = new jsPDF(orientation, 'mm', 'a4');

        // Add image to PDF
        pdf.addImage(imgData, 'PNG', margin, margin, contentWidth, scaledHeight);

        // Download
        pdf.save(`${containerId}_flowchart.pdf`);
    });
}

// =============================================================================
// PARSE DIAGRAM FROM BLUEPRINT
// =============================================================================

function parseDiagramFromBlueprint(blueprint) {
    // Try to get diagram schema from blueprint
    const diagrams = {
        userFlow: null,
        techStack: null
    };

    // Check if blueprint has diagram_schema field
    if (blueprint.diagram_schema) {
        diagrams.userFlow = blueprint.diagram_schema.user_flow || null;
        diagrams.techStack = blueprint.diagram_schema.tech_stack || null;
    }

    // Try to infer from existing blueprint data if no schema
    if (!diagrams.userFlow && blueprint.systemFlow) {
        diagrams.userFlow = inferUserFlowFromBlueprint(blueprint);
    }

    if (!diagrams.techStack && blueprint.techStack) {
        diagrams.techStack = inferTechStackFromBlueprint(blueprint);
    }

    return diagrams;
}

function inferUserFlowFromBlueprint(blueprint) {
    const nodes = [];
    const edges = [];

    // Try to extract from systemFlow - but create BRANCHING structure
    const flow = blueprint.systemFlow;
    if (flow && flow.steps && Array.isArray(flow.steps) && flow.steps.length >= 3) {
        const steps = flow.steps;
        const midPoint = Math.floor(steps.length / 2);

        // Level 0: Entry point
        nodes.push({
            id: 'entry',
            label: steps[0].action || steps[0].actor || 'Start',
            tags: ['START']
        });

        // Level 1: First few steps as parallel branches
        const level1Steps = steps.slice(1, Math.min(4, midPoint));
        level1Steps.forEach((step, idx) => {
            const id = `step1_${idx}`;
            nodes.push({
                id,
                label: step.action || step.actor || `Step ${idx + 1}`,
                tags: idx === 0 ? ['IN PROGRESS'] : []
            });
            edges.push(['entry', id]);
        });

        // Level 2: Middle steps converge to core action
        nodes.push({
            id: 'core',
            label: steps[midPoint]?.action || 'Process',
            tags: ['ATTENTION']
        });
        level1Steps.forEach((_, idx) => {
            edges.push([`step1_${idx}`, 'core']);
        });

        // Level 3: Outcome branches
        if (steps.length > midPoint + 1) {
            nodes.push({
                id: 'success',
                label: steps[steps.length - 1]?.action || 'Complete',
                tags: ['DONE']
            });
            nodes.push({
                id: 'retry',
                label: 'Retry / Adjust',
                tags: ['REVIEW']
            });
            edges.push(['core', 'success']);
            edges.push(['core', 'retry']);
            edges.push(['retry', 'entry']);
        }
    } else if (nodes.length === 0 && blueprint.featuresDetailed?.features) {
        // Build from features with branching
        const features = blueprint.featuresDetailed.features.slice(0, 6);

        // Entry
        nodes.push({ id: 'login', label: 'User Login', tags: ['START'] });

        // Features as parallel branches (Level 1)
        features.slice(0, 3).forEach((f, idx) => {
            const id = `feature_${idx}`;
            nodes.push({ id, label: f.feature_name || `Feature ${idx + 1}`, tags: ['IN PROGRESS'] });
            edges.push(['login', id]);
        });

        // Result node (Level 2)
        nodes.push({ id: 'result', label: 'View Result', tags: ['DONE'] });
        features.slice(0, 3).forEach((_, idx) => {
            edges.push([`feature_${idx}`, 'result']);
        });
    }

    return nodes.length > 0 ? { nodes, edges } : null;
}

function inferTechStackFromBlueprint(blueprint) {
    const nodes = [];
    const edges = [];
    const seenTypes = new Set();

    if (blueprint.techStack && Array.isArray(blueprint.techStack)) {
        blueprint.techStack.forEach((tech, idx) => {
            const category = (tech.category || 'other').toLowerCase();
            let type = 'backend';

            if (category.includes('frontend') || category.includes('ui')) type = 'frontend';
            else if (category.includes('database') || category.includes('storage')) type = 'database';
            else if (category.includes('api') || category.includes('external')) type = 'external';
            else if (category.includes('auth')) type = 'auth';

            // Avoid duplicates by type
            if (!seenTypes.has(type)) {
                seenTypes.add(type);
                nodes.push({
                    id: type,
                    label: tech.technology || type,
                    type: type
                });
            }
        });

        // Create standard edges
        if (seenTypes.has('frontend')) {
            if (seenTypes.has('backend')) edges.push(['frontend', 'backend']);
            else if (seenTypes.has('database')) edges.push(['frontend', 'database']);
        }
        if (seenTypes.has('backend')) {
            if (seenTypes.has('database')) edges.push(['backend', 'database']);
            if (seenTypes.has('external')) edges.push(['backend', 'external']);
            if (seenTypes.has('auth')) edges.push(['backend', 'auth']);
        }
    }

    return nodes.length > 0 ? { nodes, edges } : null;
}

// =============================================================================
// INITIALIZATION
// =============================================================================

function initFlowcharts(blueprint) {
    const diagrams = parseDiagramFromBlueprint(blueprint || {});

    // Render User Flow
    renderFlowchart('userFlowDiagram', diagrams.userFlow, true);

    // Render Tech Stack
    renderFlowchart('techStackDiagram', diagrams.techStack, false);
}

// Make functions globally available
window.renderFlowchart = renderFlowchart;
window.initFlowcharts = initFlowcharts;
window.exportFlowchartAsPNG = exportFlowchartAsPNG;
window.exportFlowchartAsPDF = exportFlowchartAsPDF;
window.parseDiagramFromBlueprint = parseDiagramFromBlueprint;
