/**
 * AI Project Planner - Main Application JavaScript
 * ==================================================
 * 
 * This file handles all frontend functionality:
 * - API communication with the backend
 * - Form handling and validation
 * - State management for the planning process
 * - Mermaid diagram rendering
 * - Export functionality
 * 
 * Design principle: Keep it simple and readable for students.
 */

// ==========================================================
// CONFIGURATION
// ==========================================================

/**
 * API Configuration
 * 
 * DEPLOYMENT SETUP:
 * 1. Replace PRODUCTION_API_URL with your actual Render backend URL
 * 2. Or set window.VITE_API_BASE_URL before this script loads
 */
const PRODUCTION_API_URL = 'https://blueprintai-backend.onrender.com'; // TODO: Update with your Render URL

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : (window.VITE_API_BASE_URL || PRODUCTION_API_URL);

/**
 * Application State
 * Stores all data from the planning process
 */
const appState = {
    // Current mode: 'idle', 'loading', 'chat', 'dashboard'
    mode: 'idle',

    // Planning state machine: IDLE, IDEATION, FINALIZED, GENERATING, GENERATED, REVISING
    planningState: 'IDLE',

    // Original idea from the user
    rawIdea: '',

    // Planning mode: 'interactive' or 'ai_only'
    planningMode: 'interactive',

    // Expanded idea details
    expandedIdea: null,

    // Feasibility evaluation
    evaluation: null,

    // Chat messages for interactive mode (context only, NOT blueprint content)
    chatMessages: [],

    // Chat history for API calls [{role, content}]
    chatHistory: [],

    // Draft summary during IDEATION (not final until confirmed)
    draftSummary: null,

    // Current questions (interactive mode)
    currentQuestions: [],

    // Complete blueprint
    blueprint: {
        projectTitle: '',
        projectSubtitle: '',
        abstract: '',
        ideaSummary: '',
        evaluation: null,
        features: [],
        featuresDetailed: null,  // NEW: Detailed feature breakdown
        featureTradeoffs: [],
        systemFlow: null,
        techStack: [],
        techStackExtended: null, // NEW: Extended tech stack with explanations & backups
        architecture: null,
        userFlowMermaid: '',
        techStackMermaid: '',
        comparison: null,        // NEW: Comparison with existing solutions
        vivaGuide: null,
        hackathonViva: null,     // NEW: Extended viva with hackathon questions
        pitch: null,
        limitations: [],
        futureScope: []
    }
};

// ==========================================================
// BLUEPRINT CACHE & LOADING STATES
// ==========================================================

/**
 * Cache for generated blueprints
 * Key: hash of idea + mode
 * Value: blueprint response
 */
const blueprintCache = {};

/**
 * Progressive loading messages for better perceived performance
 */
const LOADING_MESSAGES = [
    'Analyzing your idea…',
    'Identifying key features…',
    'Generating system structure…',
    'Building tech recommendations…',
    'Preparing diagrams & viva content…',
    'Almost there…'
];

/**
 * Simple hash function for cache keys
 */
function hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString(16);
}

/**
 * Get cache key for a blueprint request
 */
function getCacheKey(idea, mode) {
    return hashString(`${idea.trim().toLowerCase()}|${mode}`);
}

/**
 * Start animated loading text
 * Returns interval ID for cleanup
 */
let loadingAnimationInterval = null;
function startLoadingAnimation() {
    const loadingText = document.querySelector('.loading-text');
    if (!loadingText) return;

    let index = 0;
    loadingText.textContent = LOADING_MESSAGES[0];

    loadingAnimationInterval = setInterval(() => {
        index = (index + 1) % LOADING_MESSAGES.length;
        loadingText.textContent = LOADING_MESSAGES[index];
    }, 2500);
}

function stopLoadingAnimation() {
    if (loadingAnimationInterval) {
        clearInterval(loadingAnimationInterval);
        loadingAnimationInterval = null;
    }
}

// ==========================================================
// UTILITY FUNCTIONS
// ==========================================================

/**
 * Make an API request to the backend
 * 
 * @param {string} endpoint - API endpoint (e.g., '/api/idea')
 * @param {string} method - HTTP method (GET, POST, etc.)
 * @param {object} data - Data to send (for POST requests)
 * @returns {Promise<object>} - API response
 */
async function apiRequest(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();

        return result;
    } catch (error) {
        console.error('API Error:', error);
        return {
            success: false,
            message: 'Could not connect to the server.',
            errors: ['Make sure the backend is running on ' + API_BASE_URL]
        };
    }
}

/**
 * Show an element by removing the 'hidden' class
 */
function showElement(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
}

/**
 * Hide an element by adding the 'hidden' class
 */
function hideElement(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}

/**
 * Store data in localStorage for persistence
 */
function saveState() {
    try {
        localStorage.setItem('projectPlannerState', JSON.stringify(appState));
    } catch (e) {
        console.warn('Could not save state:', e);
    }
}

/**
 * Load data from localStorage
 */
function loadState() {
    try {
        const saved = localStorage.getItem('projectPlannerState');
        if (saved) {
            Object.assign(appState, JSON.parse(saved));
        }
    } catch (e) {
        console.warn('Could not load state:', e);
    }
}

/**
 * Save blueprint-specific state to localStorage
 * Blueprint persistence is handled client-side to ensure instant navigation,
 * offline safety, and zero backend dependency.
 * 
 * @param {string} activeTab - The currently active tab ID (default: 'summary')
 */
function saveBlueprintState(activeTab = 'summary') {
    try {
        // Only save if we have a valid blueprint
        if (!appState.blueprint || !appState.rawIdea) return;

        localStorage.setItem('blueprintAI_state', JSON.stringify({
            version: 1, // Version guard for future schema changes
            blueprint: appState.blueprint,
            expandedIdea: appState.expandedIdea,
            rawIdea: appState.rawIdea,
            activeTab: activeTab,
            timestamp: Date.now()
        }));
    } catch (e) {
        console.warn('Could not save blueprint state:', e);
    }
}

/**
 * Restore blueprint state from localStorage
 * @returns {Object|false} - { restored: true, activeTab } if successful, false otherwise
 */
function restoreBlueprintState() {
    try {
        const saved = localStorage.getItem('blueprintAI_state');
        if (!saved) return false;

        const parsed = JSON.parse(saved);

        // Version guard - only restore if schema matches
        if (parsed.version !== 1) return false;
        if (!parsed?.blueprint || !parsed?.rawIdea) return false;

        // Restore to appState
        appState.blueprint = parsed.blueprint;
        appState.expandedIdea = parsed.expandedIdea;
        appState.rawIdea = parsed.rawIdea;

        console.log('📦 Blueprint restored from localStorage');
        return {
            restored: true,
            activeTab: parsed.activeTab || 'summary'
        };
    } catch (e) {
        console.warn('Could not restore blueprint state:', e);
        return false;
    }
}

/**
 * Clear saved state and reset for new idea (without page reload)
 * This preserves the UI structure and just clears the content
 */
function startOver() {
    // Clear localStorage (both general state and blueprint-specific state)
    localStorage.removeItem('projectPlannerState');
    localStorage.removeItem('blueprintAI_state');

    // Clear session storage (chat initialization flag)
    sessionStorage.removeItem('mentor_chat_initialized');

    // Reset appState to initial values
    appState.mode = 'idle';
    appState.planningState = 'IDLE';
    appState.rawIdea = '';
    appState.planningMode = 'interactive';
    appState.expandedIdea = null;
    appState.evaluation = null;
    appState.chatMessages = [];
    appState.chatHistory = [];
    appState.draftSummary = null;
    appState.currentQuestions = [];
    appState.blueprint = {
        projectTitle: '',
        projectSubtitle: '',
        abstract: '',
        ideaSummary: '',
        evaluation: null,
        features: [],
        featuresDetailed: null,
        featureTradeoffs: [],
        systemFlow: null,
        techStack: [],
        techStackExtended: null,
        architecture: null,
        userFlowMermaid: '',
        techStackMermaid: '',
        comparison: null,
        vivaGuide: null,
        hackathonViva: null,
        pitch: null,
        limitations: [],
        futureScope: []
    };

    // Clear all content containers
    const contentIds = [
        'ideaSummary', 'featuresContent', 'feasibilityContent',
        'systemFlowContent', 'techStackContent', 'diagramsContent',
        'comparisonContent', 'vivaContent', 'pitchContent'
    ];

    contentIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            // Reset to empty state for summary tab
            if (id === 'ideaSummary') {
                el.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">💡</div>
                        <h3 class="empty-title">No Blueprint Yet</h3>
                        <p class="empty-text">Start with even a rough idea — clarity comes step by step.</p>
                        <a href="index.html" class="btn btn-primary">Start Planning</a>
                    </div>
                `;
            } else {
                el.innerHTML = '';
            }
        }
    });

    // Clear diagram containers specifically
    const userFlowDiagram = document.getElementById('userFlowDiagram');
    const techStackDiagram = document.getElementById('techStackDiagram');
    if (userFlowDiagram) userFlowDiagram.innerHTML = '';
    if (techStackDiagram) techStackDiagram.innerHTML = '';

    // Update project title
    const titleEl = document.getElementById('projectTitle');
    if (titleEl) titleEl.textContent = 'Your Project Blueprint';

    // Switch to summary tab
    const summaryBtn = document.querySelector('.tab-btn[data-tab="summary"]');
    if (summaryBtn) summaryBtn.click();

    console.log('🔄 Blueprint cleared. Ready for new idea.');
}

// Keep clearState as alias for backward compatibility
function clearState() {
    startOver();
}

// ==========================================================
// STATE MACHINE FUNCTIONS
// ==========================================================

/**
 * Get current planning state
 */
function getPlanningState() {
    return appState.planningState || 'IDLE';
}

/**
 * Set planning state with validation
 */
function setPlanningState(newState) {
    const validStates = ['IDLE', 'IDEATION', 'FINALIZED', 'GENERATING', 'GENERATED', 'REVISING'];
    if (validStates.includes(newState)) {
        appState.planningState = newState;
        console.log(`📌 Planning state: ${newState}`);
        saveState();
    }
}

/**
 * Transition to IDEATION state (start interactive chat)
 */
function transitionToIdeation() {
    setPlanningState('IDEATION');
    appState.chatHistory = [];
    appState.draftSummary = null;
}

/**
 * Transition to FINALIZED state (lock draft summary)
 */
function transitionToFinalized() {
    if (!appState.draftSummary) {
        console.warn('Cannot finalize: no draft summary');
        return false;
    }
    setPlanningState('FINALIZED');
    // Copy draft to expandedIdea for blueprint generation
    appState.expandedIdea = {
        problem_statement: appState.draftSummary.problem_statement || appState.rawIdea,
        objectives: appState.draftSummary.main_features || [],
        target_users: appState.draftSummary.target_users || ''
    };
    saveState();
    return true;
}

/**
 * Transition to GENERATING state
 */
function transitionToGenerating() {
    setPlanningState('GENERATING');
}

/**
 * Transition to GENERATED state
 */
function transitionToGenerated() {
    setPlanningState('GENERATED');
}

/**
 * Transition to REVISING state
 */
function transitionToRevising() {
    setPlanningState('REVISING');
}

// ==========================================================
// CHAT API FUNCTIONS
// ==========================================================

/**
 * Send a message in interactive planning mode
 */
async function sendChatMessage(userMessage) {
    if (!userMessage || userMessage.trim().length < 2) {
        return { success: false, error: 'Message too short' };
    }

    // Add user message to display
    appState.chatMessages.push({
        role: 'user',
        content: userMessage
    });

    // Build chat history for API
    appState.chatHistory.push({
        role: 'user',
        content: userMessage
    });

    try {
        const result = await apiRequest('/api/chat/message', 'POST', {
            raw_idea: appState.rawIdea,
            chat_history: appState.chatHistory,
            user_message: userMessage
        });

        if (result.success && result.data) {
            // Add AI response to display
            appState.chatMessages.push({
                role: 'ai',
                content: result.data.ai_response
            });

            // Add to history for next call
            appState.chatHistory.push({
                role: 'ai',
                content: result.data.ai_response
            });

            // Update draft summary
            if (result.data.draft_summary) {
                appState.draftSummary = result.data.draft_summary;
            }

            saveState();
            return {
                success: true,
                data: result.data
            };
        } else {
            return { success: false, error: result.message || 'Failed to get response' };
        }
    } catch (error) {
        console.error('Chat error:', error);
        return { success: false, error: 'Connection error' };
    }
}

/**
 * Start a new chat session
 */
async function startChatSession() {
    transitionToIdeation();

    try {
        const result = await apiRequest('/api/chat/start', 'POST', null, `?raw_idea=${encodeURIComponent(appState.rawIdea)}`);

        if (result.success && result.data) {
            appState.chatMessages.push({
                role: 'ai',
                content: result.data.ai_response
            });
            appState.chatHistory.push({
                role: 'ai',
                content: result.data.ai_response
            });
            if (result.data.draft_summary) {
                appState.draftSummary = result.data.draft_summary;
            }
            saveState();
            return { success: true, data: result.data };
        }
    } catch (error) {
        console.error('Failed to start chat:', error);
    }

    // Fallback greeting
    const greeting = `Great! Let's plan your project: "${appState.rawIdea}"\n\nCan you tell me more about who will use this and what problem it solves?`;
    appState.chatMessages.push({ role: 'ai', content: greeting });
    appState.draftSummary = {
        problem_statement: appState.rawIdea,
        target_users: '',
        main_features: [],
        scope_notes: 'Not yet defined'
    };
    saveState();
    return { success: true };
}

/**
 * Apply a change request to the blueprint
 */
async function applyChangeRequest(changeRequest) {
    if (!changeRequest || changeRequest.trim().length < 5) {
        return { success: false, error: 'Please describe the change' };
    }

    transitionToRevising();

    // Build current summary from blueprint
    const currentSummary = {
        problem_statement: appState.blueprint.ideaSummary || appState.rawIdea,
        target_users: appState.expandedIdea?.target_users || '',
        main_features: appState.blueprint.features || [],
        scope_notes: ''
    };

    try {
        const result = await apiRequest('/api/revision/apply', 'POST', {
            current_summary: currentSummary,
            change_request: changeRequest.trim()
        });

        if (result.success && result.data) {
            // Update summary
            if (result.data.updated_summary) {
                appState.expandedIdea = {
                    problem_statement: result.data.updated_summary.problem_statement,
                    objectives: result.data.updated_summary.main_features || [],
                    target_users: result.data.updated_summary.target_users
                };
                appState.blueprint.ideaSummary = result.data.updated_summary.problem_statement;
            }

            saveState();
            transitionToGenerated();

            return {
                success: true,
                data: result.data
            };
        } else {
            transitionToGenerated(); // Revert state on failure
            return { success: false, error: result.message };
        }
    } catch (error) {
        transitionToGenerated();
        return { success: false, error: 'Failed to apply change' };
    }
}

/**
 * Save project to Firestore via backend API
 * This persists the blueprint to the database for future reference
 */
async function saveToFirestore() {
    try {
        const result = await apiRequest('/api/export/blueprint', 'POST', {
            project_title: appState.blueprint.projectTitle || 'Untitled Project',
            idea_input: appState.rawIdea,
            mode: appState.planningMode,
            sections: {
                evaluation: appState.blueprint.evaluation,
                systemFlow: appState.blueprint.systemFlow,
                techStack: appState.blueprint.techStack,
                vivaGuide: appState.blueprint.vivaGuide,
                pitch: appState.blueprint.pitch,
                expandedIdea: appState.expandedIdea
            },
            user_flow_mermaid: appState.blueprint.userFlowMermaid || '',
            tech_stack_mermaid: appState.blueprint.techStackMermaid || ''
        });

        if (result.success && result.data?.project_id) {
            console.log('✅ Project saved to database:', result.data.project_id);
        } else {
            console.warn('⚠️ Project not saved to database (this is okay if Firebase is not configured)');
        }
    } catch (error) {
        // Non-blocking - don't crash if save fails
        console.warn('Could not save to database:', error);
    }
}

// ==========================================================
// IDEA FORM HANDLING
// ==========================================================

/**
 * Initialize the idea form on the home page
 */
function initIdeaForm() {
    const form = document.getElementById('ideaForm');
    const textarea = document.getElementById('ideaInput');
    const charCount = document.getElementById('charCount');
    const submitBtn = document.getElementById('submitBtn');

    if (!form) return; // Not on home page

    // Update character count as user types
    if (textarea && charCount) {
        textarea.addEventListener('input', () => {
            charCount.textContent = textarea.value.length;
        });
    }

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const rawIdea = textarea.value.trim();
        const planningMode = document.querySelector('input[name="planningMode"]:checked')?.value || 'interactive';

        if (rawIdea.length < 10) {
            showError('Your idea is too short.', 'Please describe your project in at least one complete sentence.');
            return;
        }

        // Disable button to prevent duplicate clicks
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Generating...';
        }

        // Save to state
        appState.rawIdea = rawIdea;
        appState.planningMode = planningMode;

        // Show loading state
        hideElement('ideaForm');
        showElement('loadingState');
        hideElement('errorMessage');

        // Submit to API
        const result = await apiRequest('/api/idea', 'POST', {
            raw_idea: rawIdea,
            mode: planningMode
        });

        hideElement('loadingState');

        if (result.success) {
            // Store the response
            if (planningMode === 'interactive') {
                // Store questions and go to chat page
                appState.currentQuestions = result.data.questions || [];
                saveState();
                window.location.href = 'chat.html';
            } else {
                // AI_only mode - go directly to expanding
                appState.expandedIdea = result.data.expanded;

                // Continue with evaluation
                await generateFullBlueprint();
            }
        } else {
            showElement('ideaForm');
            // Re-enable button on error
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = '✨ Generate My Blueprint';
            }
            showError(result.message, result.errors?.[0] || 'Please try again.');
        }
    });
}

/**
 * Display an error message
 */
function showError(title, suggestion) {
    const errorEl = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    const errorSuggestion = document.getElementById('errorSuggestion');

    if (errorEl && errorText) {
        errorText.textContent = title;
        if (errorSuggestion) {
            errorSuggestion.textContent = suggestion || '';
        }
        showElement('errorMessage');
    }
}

/**
 * Generate the full blueprint (for AI_only mode)
 * 
 * Features:
 * - Client-side caching to avoid redundant API calls
 * - Progressive loading states for better perceived performance
 * - Provider cascade (Gemini → GPT → Groq) handles failures automatically.
 */
async function generateFullBlueprint() {
    const idea = appState.expandedIdea?.problem_statement || appState.rawIdea;
    const mode = 'QUICK_BLUEPRINT';
    const cacheKey = getCacheKey(idea, mode);

    // Check cache first
    if (blueprintCache[cacheKey]) {
        console.log('📦 Blueprint loaded from cache');
        applyBlueprintData(blueprintCache[cacheKey]);
        return;
    }

    showElement('loadingState');
    startLoadingAnimation();

    try {
        // Single call to unified blueprint endpoint
        const result = await apiRequest('/api/planning/generate-blueprint', 'POST', {
            idea: idea,
            mode: mode
        });

        stopLoadingAnimation();

        if (result.success && result.data?.blueprint) {
            // Cache the successful response
            blueprintCache[cacheKey] = result.data.blueprint;

            // Apply the blueprint data
            applyBlueprintData(result.data.blueprint);
        } else {
            // Handle failure gracefully
            hideElement('loadingState');
            showElement('ideaForm');
            showError(
                result.message || 'The AI service is temporarily unavailable.',
                'Please try again in a moment.'
            );
        }

    } catch (error) {
        console.error('Blueprint generation error:', error);
        stopLoadingAnimation();
        hideElement('loadingState');
        showElement('ideaForm');
        showError('Something went wrong.', 'Please check if the backend server is running.');
    }
}

/**
 * Apply blueprint data to appState and redirect to dashboard
 */
function applyBlueprintData(bp) {
    // Summary/expanded idea
    if (bp.expandedIdea) {
        appState.expandedIdea = appState.expandedIdea || {};
        Object.assign(appState.expandedIdea, bp.expandedIdea);
    }

    // All blueprint sections
    appState.blueprint.evaluation = bp.evaluation;
    appState.blueprint.featuresDetailed = bp.featuresDetailed;
    appState.blueprint.systemFlow = bp.systemFlow;
    appState.blueprint.techStack = bp.techStack;
    appState.blueprint.techStackExtended = bp.techStackExtended;
    appState.blueprint.comparison = bp.comparison;
    appState.blueprint.vivaGuide = bp.vivaGuide;
    appState.blueprint.hackathonViva = bp.hackathonViva;
    appState.blueprint.pitch = bp.pitch;
    appState.blueprint.userFlowMermaid = bp.userFlowMermaid;
    appState.blueprint.techStackMermaid = bp.techStackMermaid;

    // Build project title
    appState.blueprint.projectTitle = generateProjectTitle();
    appState.blueprint.ideaSummary = appState.expandedIdea?.problem_statement || appState.rawIdea;

    // Save to localStorage
    saveState();

    // Save dedicated blueprint state for persistence across navigation
    saveBlueprintState('summary');

    // Save to Firestore (backend persistence) - non-blocking
    saveToFirestore();

    // Redirect to dashboard
    window.location.href = 'dashboard.html';
}

/**
 * Generate a project title from the idea
 */
function generateProjectTitle() {
    const idea = appState.rawIdea.toLowerCase();

    // Try to extract a meaningful title
    if (idea.includes('attendance')) return 'Smart Attendance System';
    if (idea.includes('agriculture') || idea.includes('farming')) return 'Smart Agriculture Platform';
    if (idea.includes('health') || idea.includes('medical')) return 'Health Management System';
    if (idea.includes('library')) return 'Digital Library System';
    if (idea.includes('exam') || idea.includes('quiz')) return 'Online Examination System';
    if (idea.includes('chat') || idea.includes('message')) return 'Communication Platform';
    if (idea.includes('food') || idea.includes('restaurant')) return 'Food Ordering System';
    if (idea.includes('shop') || idea.includes('store') || idea.includes('ecommerce')) return 'E-Commerce Platform';

    // Default: capitalize first words
    const words = appState.rawIdea.split(' ').slice(0, 5);
    return words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') + ' System';
}

// ==========================================================
// CHAT PAGE HANDLING
// ==========================================================

/**
 * Initialize the chat page
 * Mentor welcome message is injected once on chat initialization.
 * This prevents duplicate messages caused by user-triggered side effects
 * or component re-renders.
 */
function initChatPage() {
    const chatContainer = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const continueBtn = document.getElementById('continueBtn');

    if (!chatContainer) return; // Not on chat page

    // Load saved state
    loadState();

    // Check if chat is already initialized (prevent duplicate messages on navigation)
    const chatAlreadyInitialized = sessionStorage.getItem('mentor_chat_initialized') === 'true';
    const hasExistingMessages = appState.chatMessages && appState.chatMessages.length > 0;

    // If we have existing messages, just render them (don't add new ones)
    if (hasExistingMessages) {
        // Re-render existing messages
        chatContainer.innerHTML = '';
        appState.chatMessages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message message-${msg.type}`;
            messageDiv.innerHTML = msg.text.replace(/\n/g, '<br>');
            chatContainer.appendChild(messageDiv);
        });
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Mark as initialized
        sessionStorage.setItem('mentor_chat_initialized', 'true');
    } else if (appState.rawIdea) {
        // First time initialization - add welcome messages IMMEDIATELY on page load
        // This happens BEFORE any user interaction
        sessionStorage.setItem('mentor_chat_initialized', 'true');

        // Display the original idea
        addMessage(`Your idea: "${appState.rawIdea}"`, 'user');

        // Display initial questions or welcome message IMMEDIATELY
        if (appState.currentQuestions && appState.currentQuestions.length > 0) {
            let questionText = "Great idea! Let me ask a few questions to understand it better:\n\n";
            appState.currentQuestions.forEach((q, i) => {
                questionText += `${i + 1}. ${q.question_text}\n`;
                if (q.context) {
                    questionText += `   (${q.context})\n`;
                }
                if (q.options && q.options.length > 0) {
                    questionText += `   Options: ${q.options.join(', ')}\n`;
                }
                questionText += '\n';
            });
            addMessage(questionText, 'ai');
        } else {
            addMessage("Great! Let's plan your project step by step. Can you tell me more about who will use this and what problem it solves?", 'ai');
        }
    }

    // Handle send button
    if (sendBtn) {
        sendBtn.addEventListener('click', handleChatSend);
    }

    // Handle enter key
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleChatSend();
            }
        });
    }

    // Handle continue button (skip to blueprint)
    if (continueBtn) {
        continueBtn.addEventListener('click', async () => {
            addMessage("Let's generate your blueprint with the information we have!", 'ai');

            // Get expanded idea if not already
            if (!appState.expandedIdea) {
                const result = await apiRequest('/api/idea/understand', 'POST', {
                    raw_idea: appState.rawIdea + '\n\nChat context:\n' +
                        appState.chatMessages.filter(m => m.type === 'user').map(m => m.text).join('\n'),
                    mode: 'interactive'
                });

                if (result.success) {
                    appState.expandedIdea = result.data.expanded;
                }
            }

            // Generate full blueprint
            await generateFullBlueprintFromChat();
        });
    }
}

/**
 * Add a message to the chat display
 */
function addMessage(text, type) {
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;

    // Format text with line breaks
    messageDiv.innerHTML = text.replace(/\n/g, '<br>');

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Store in state
    appState.chatMessages.push({ text, type });
    saveState();
}

/**
 * Handle sending a chat message
 */
async function handleChatSend() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();

    if (!message) return;

    // INSTANT: Add user message immediately (WhatsApp-like behavior)
    addMessage(message, 'user');
    chatInput.value = '';

    // Show typing indicator instead of blocking message
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message message-ai typing-indicator';
    typingDiv.innerHTML = '<span class="typing-dots">Thinking<span>.</span><span>.</span><span>.</span></span>';
    typingDiv.id = 'typing-indicator';
    const chatContainer = document.getElementById('chatMessages');
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Build context from chat history
    const context = appState.rawIdea + '\n\nStudent clarifications:\n' +
        appState.chatMessages.filter(m => m.type === 'user').map(m => m.text).join('\n');

    // Get AI response (expand or analyze trade-off based on content)
    if (message.toLowerCase().includes('add') || message.toLowerCase().includes('include')) {
        // Analyze feature trade-off
        const result = await apiRequest('/api/planning/tradeoffs', 'POST', {
            project_summary: context,
            feature: message
        });

        if (result.success && result.data.analysis) {
            const analysis = result.data.analysis;
            let response = `Here's what adding that feature means:\n\n`;
            response += `📊 Complexity: ${analysis.complexity_impact || 'Moderate'}\n`;
            response += `⏱️ Time Impact: ${analysis.time_impact || 'Some additional development time'}\n`;
            response += `🏗️ Architecture: ${analysis.architecture_impact || 'May require some changes'}\n\n`;
            response += `💡 Recommendation: ${analysis.recommendation || 'Consider carefully based on your timeline'}\n\n`;
            response += `What else would you like to know?`;

            // Remove the typing indicator
            const typingEl = document.getElementById('typing-indicator');
            if (typingEl) typingEl.remove();

            addMessage(response, 'ai');
        } else {
            // Remove typing indicator on failure too
            const typingEl = document.getElementById('typing-indicator');
            if (typingEl) typingEl.remove();
        }
    } else {
        // General response - expand understanding
        const result = await apiRequest('/api/idea/understand', 'POST', {
            raw_idea: context,
            mode: 'interactive'
        });

        if (result.success && result.data.expanded) {
            appState.expandedIdea = result.data.expanded;

            let response = `I understand better now! Here's what I see:\n\n`;
            response += `📋 Problem: ${result.data.expanded.problem_statement || 'Helping users with their needs'}\n\n`;
            response += `👥 Target Users: ${(result.data.expanded.target_users || ['Users']).join(', ')}\n\n`;
            response += `Would you like to:\n`;
            response += `• Add or remove any features?\n`;
            response += `• Continue to generate your blueprint?\n\n`;
            response += `(Click "Continue to Blueprint" when you're ready!)`;

            // Remove the typing indicator
            const typingEl = document.getElementById('typing-indicator');
            if (typingEl) typingEl.remove();

            addMessage(response, 'ai');
        }
    }
}

/**
 * Generate blueprint from chat context
 */
async function generateFullBlueprintFromChat() {
    // Disable chat input
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const continueBtn = document.getElementById('continueBtn');

    if (chatInput) chatInput.disabled = true;
    if (sendBtn) sendBtn.disabled = true;
    if (continueBtn) continueBtn.disabled = true;

    addMessage('Generating your complete blueprint... This may take a minute.', 'ai');

    try {
        // Call the same blueprint generation as AI_only mode
        // but with chat context
        await generateFullBlueprint();
    } catch (error) {
        addMessage('Oops! Something went wrong. Please check if the backend is running.', 'ai');
    }
}

// ==========================================================
// DASHBOARD PAGE HANDLING
// ==========================================================

/**
 * Initialize the dashboard page
 */
function initDashboard() {
    const dashboardContainer = document.querySelector('.dashboard-layout');
    if (!dashboardContainer) return; // Not on dashboard page

    // Load saved state from both sources
    loadState();

    // Try to restore from dedicated blueprint state
    const restored = restoreBlueprintState();

    // Check if we have data to display
    if (!appState.rawIdea && !restored) {
        dashboardContainer.innerHTML = `
            <div class="section-card" style="text-align: center; padding: 3rem;">
                <h2>No Blueprint Yet</h2>
                <p style="margin: 1rem 0;">You haven't generated a blueprint yet.</p>
                <a href="index.html" class="submit-btn" style="display: inline-flex; width: auto;">
                    Start Planning
                </a>
            </div>
        `;
        return;
    }

    // Populate the dashboard with data
    populateDashboard();

    // Initialize tabs
    initTabs();

    // Restore active tab if we have saved state
    if (restored && restored.activeTab) {
        const tabBtn = document.querySelector(`.tab-btn[data-tab="${restored.activeTab}"]`);
        if (tabBtn) tabBtn.click();
    }

    // Initialize Mermaid for diagrams
    initMermaid();

    // Initialize viva Q&A toggles
    initVivaToggles();
}

/**
 * Populate dashboard with blueprint data
 */
function populateDashboard() {
    // Project Title
    const titleEl = document.getElementById('projectTitle');
    if (titleEl) {
        titleEl.textContent = appState.blueprint.projectTitle || 'Your Project';
    }

    // Idea Summary
    const summaryEl = document.getElementById('ideaSummary');
    if (summaryEl && appState.expandedIdea) {
        summaryEl.innerHTML = `
            <h4>Problem Statement</h4>
            <p>${appState.expandedIdea.problem_statement || appState.rawIdea}</p>
            
            <h4>Target Users</h4>
            <ul class="strength-list">
                ${(appState.expandedIdea.target_users || ['Users']).map(u => `<li>👤 ${u}</li>`).join('')}
            </ul>
            
            <h4>Objectives</h4>
            <ul class="strength-list">
                ${(appState.expandedIdea.objectives || ['Solve the problem']).map(o => `<li>🎯 ${o}</li>`).join('')}
            </ul>
            
            <h4>Scope</h4>
            <p>${appState.expandedIdea.scope || 'Defined by project requirements'}</p>
            
            <div class="education-note">
                <strong>💡 What this means:</strong>
                ${appState.expandedIdea.what_this_means || 'This structure helps you explain your project clearly in any review.'}
            </div>
        `;
    }

    // Feasibility & Risks
    const feasibilityEl = document.getElementById('feasibilityContent');
    if (feasibilityEl && appState.blueprint.evaluation) {
        const eval_ = appState.blueprint.evaluation;
        feasibilityEl.innerHTML = `
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                <span style="font-size: 2rem;">
                    ${eval_.feasibility_level === 'High' ? '✅' : eval_.feasibility_level === 'Medium' ? '⚠️' : '❌'}
                </span>
                <div>
                    <strong style="font-size: 1.25rem;">Feasibility: ${eval_.feasibility_level || 'Medium'}</strong>
                    <p style="color: var(--color-text-secondary); margin-top: 0.25rem;">
                        ${eval_.feasibility_explanation || 'This project is suitable for a college student.'}
                    </p>
                </div>
            </div>
            
            <h4>✅ Strengths</h4>
            <ul class="strength-list">
                ${(eval_.strengths || ['Good idea']).map(s => `<li>💪 ${s}</li>`).join('')}
            </ul>
            
            <h4>⚠️ Risks to Consider</h4>
            <ul class="risk-list">
                ${(eval_.risks || ['Standard development challenges']).map(r => `<li>⚡ ${r}</li>`).join('')}
            </ul>
            
            <div class="education-note">
                <strong>💡 Why this matters:</strong>
                ${eval_.why_this_matters || 'Knowing your project\'s strengths and risks helps you plan realistically.'}
            </div>
        `;
    }

    // Features (NEW)
    const featuresEl = document.getElementById('featuresContent');
    if (featuresEl && appState.blueprint.featuresDetailed) {
        const features = appState.blueprint.featuresDetailed.features || [];
        featuresEl.innerHTML = `
            <div class="features-grid" style="display: grid; gap: 1rem;">
                ${features.map(f => `
                    <div class="feature-card" style="padding: 1.25rem; background: white; border: 1px solid var(--color-border); border-radius: 10px;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
                            <span style="font-size: 1.5rem;">✨</span>
                            <strong style="font-size: 1.1rem;">${f.feature_name || 'Feature'}</strong>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: var(--color-primary); font-size: 0.8rem;">WHAT IT DOES</strong>
                            <p style="margin-top: 0.25rem;">${f.what_it_does || 'Description not available.'}</p>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: var(--color-primary); font-size: 0.8rem;">WHY IT EXISTS</strong>
                            <p style="margin-top: 0.25rem; color: var(--color-text-secondary);">${f.why_it_exists || 'Addresses a user need.'}</p>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: var(--color-primary); font-size: 0.8rem;">HOW IT HELPS</strong>
                            <p style="margin-top: 0.25rem; color: var(--color-text-secondary);">${f.how_it_helps || 'Improves user experience.'}</p>
                        </div>
                        ${f.limitations ? `
                            <div style="padding: 0.5rem; background: #fff3cd; border-radius: 6px; font-size: 0.85rem;">
                                <strong>⚠️ Limitations:</strong> ${f.limitations}
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    // System Flow
    const flowEl = document.getElementById('systemFlowContent');
    if (flowEl && appState.blueprint.systemFlow) {
        const flow = appState.blueprint.systemFlow;
        flowEl.innerHTML = `
            <h4>${flow.flow_title || 'System Flow'}</h4>
            <div class="flow-steps">
                ${(flow.steps || []).map(s => `
                    <div class="flow-step" style="display: flex; gap: 1rem; margin-bottom: 1rem; padding: 1rem; background: white; border-radius: 8px;">
                        <div style="width: 40px; height: 40px; background: var(--color-primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">
                            ${s.step_number}
                        </div>
                        <div>
                            <strong>${s.actor}: ${s.action}</strong>
                            <p style="font-size: 0.875rem; color: var(--color-text-secondary); margin-top: 0.25rem;">
                                ${s.explanation || ''}
                            </p>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <p style="margin-top: 1rem; padding: 1rem; background: var(--color-surface); border-radius: 8px;">
                <strong>Summary:</strong> ${flow.summary || 'This is how your system works, step by step.'}
            </p>
        `;
    }

    // Tech Stack
    const techEl = document.getElementById('techStackContent');
    if (techEl && appState.blueprint.techStack) {
        let techHTML = `
            <h4>🛠️ Primary Technologies</h4>
            <div class="tech-grid" style="display: grid; gap: 1rem;">
                ${appState.blueprint.techStack.map(t => `
                    <div style="padding: 1rem; background: white; border: 1px solid var(--color-border); border-radius: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>${t.technology || 'Technology'}</strong>
                            <span style="background: var(--color-primary-light); color: var(--color-primary); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">
                                ${t.category || 'General'}
                            </span>
                        </div>
                        <p style="font-size: 0.875rem; color: var(--color-text-secondary); margin-top: 0.5rem;">
                            ${t.justification || 'Suitable for this project'}
                        </p>
                        <span style="font-size: 0.75rem; color: var(--color-text-muted);">
                            ${t.skill_level || 'Beginner-friendly'}
                        </span>
                    </div>
                `).join('')}
            </div>
        `;

        // Extended tech stack with alternatives (if available)
        if (appState.blueprint.techStackExtended && appState.blueprint.techStackExtended.alternatives) {
            techHTML += `
                <h4 style="margin-top: 2rem;">🔄 Backup & Alternatives</h4>
                <div style="display: grid; gap: 1rem;">
                    ${appState.blueprint.techStackExtended.alternatives.map(alt => `
                        <div style="padding: 1rem; background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px;">
                            <strong>${alt.category}</strong>
                            <p style="margin-top: 0.5rem; font-size: 0.9rem;">
                                <strong>Primary:</strong> ${alt.primary} → 
                                <strong>Alternative:</strong> ${alt.alternative}
                            </p>
                            <p style="font-size: 0.85rem; color: var(--color-text-secondary); margin-top: 0.5rem;">
                                <strong>When to switch:</strong> ${alt.when_to_switch}
                            </p>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        techEl.innerHTML = techHTML;
    }

    // Render Flowchart Diagrams (User Flow + Tech Stack)
    // Uses new HTML/SVG flowchart system (replaces Mermaid)
    if (typeof initFlowcharts === 'function') {
        initFlowcharts(appState.blueprint);
    }

    // Comparison & Uniqueness (NEW)
    const comparisonEl = document.getElementById('comparisonContent');
    if (comparisonEl && appState.blueprint.comparison) {
        const comp = appState.blueprint.comparison;
        comparisonEl.innerHTML = `
            <h4>📊 Existing Solutions</h4>
            <p style="color: var(--color-text-secondary); margin-bottom: 1rem;">
                Here are similar solutions that already exist for this type of project:
            </p>
            <div style="display: grid; gap: 1rem; margin-bottom: 2rem;">
                ${(comp.existing_solutions || []).map(sol => `
                    <div style="padding: 1rem; background: white; border: 1px solid var(--color-border); border-radius: 8px;">
                        <strong style="color: var(--color-primary);">${sol.solution_name}</strong>
                        <p style="margin-top: 0.5rem;">${sol.what_it_does}</p>
                        <div style="margin-top: 0.75rem;">
                            <strong style="font-size: 0.85rem;">Common Features:</strong>
                            <p style="font-size: 0.9rem; color: var(--color-text-secondary);">${sol.common_features}</p>
                        </div>
                        <div style="margin-top: 0.5rem; padding: 0.5rem; background: #fff3cd; border-radius: 4px; font-size: 0.85rem;">
                            <strong>⚠️ Limitations:</strong> ${sol.limitations}
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <h4>✨ What Makes Your Project Unique</h4>
            <ul class="strength-list" style="margin-bottom: 1.5rem;">
                ${(comp.unique_aspects || ['Your project has unique aspects']).map(u => `<li>🌟 ${u}</li>`).join('')}
            </ul>
            
            <h4>💡 Why This Project Still Matters</h4>
            <ul class="strength-list" style="margin-bottom: 1.5rem;">
                ${(comp.why_still_valuable || ['This project provides learning value']).map(v => `<li>✓ ${v}</li>`).join('')}
            </ul>
            
            <div style="padding: 1rem; background: linear-gradient(135deg, #e0f2fe, #ddd6fe); border-radius: 10px; border-left: 4px solid var(--color-primary);">
                <strong>🎤 For Your Viva Defense:</strong>
                <p style="margin-top: 0.5rem; font-style: italic;">
                    "${comp.summary_insight || 'Even though similar systems exist, this project is valuable because I am solving the problem in a new way, tailored to specific needs.'}"
                </p>
            </div>
        `;
    }

    // Viva Guide (Updated with Hackathon section)
    const vivaEl = document.getElementById('vivaContent');
    if (vivaEl) {
        let vivaHTML = '';

        // Standard Viva content
        if (appState.blueprint.vivaGuide) {
            const viva = appState.blueprint.vivaGuide;
            vivaHTML += `
                <div class="section-card">
                    <h4>📋 How to Explain Your Project</h4>
                    <p>${viva.project_overview_explanation || 'This project solves a real problem using modern technology.'}</p>
                </div>
                
                <div class="section-card">
                    <h4>🎯 Problem Statement Explanation</h4>
                    <p>${viva.problem_statement_explanation || 'Explain the problem clearly and why it needs to be solved.'}</p>
                </div>
                
                <div class="section-card">
                    <h4>🏗️ Architecture Explanation</h4>
                    <p>${viva.architecture_explanation || 'The system uses a standard three-tier architecture.'}</p>
                </div>
                
                <div class="section-card">
                    <h4>⭐ Unique Features</h4>
                    <p>${viva.unique_feature_explanation || 'What makes your project special.'}</p>
                </div>
                
                <h3 style="margin-top: 2rem; margin-bottom: 1rem;">❓ Common Viva Questions</h3>
                <div id="vivaQuestions">
                    ${(viva.common_questions || []).map((q, i) => `
                        <div class="viva-qa">
                            <div class="viva-question" data-index="${i}">
                                <span>Q: ${q.question}</span>
                                <span class="toggle-icon">▼</span>
                            </div>
                            <div class="viva-answer" id="answer-${i}">
                                <p><strong>Suggested Answer:</strong></p>
                                <p>${q.suggested_answer}</p>
                                <div class="why-asked">
                                    <strong>Why examiners ask this:</strong> ${q.why_asked || 'Common question to assess understanding.'}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Hackathon-specific content (NEW)
        if (appState.blueprint.hackathonViva) {
            const hack = appState.blueprint.hackathonViva;
            vivaHTML += `
                <h3 style="margin-top: 2.5rem; margin-bottom: 1rem; padding-top: 1.5rem; border-top: 2px solid var(--color-border);">
                    🏆 Hackathon Preparation
                </h3>
                <p style="color: var(--color-text-secondary); margin-bottom: 1rem;">
                    Questions commonly asked at hackathon presentations and demo days:
                </p>
                <div id="hackathonQuestions">
                    ${(hack.hackathon_questions || []).map((q, i) => `
                        <div class="viva-qa hackathon-qa" style="border-left: 3px solid #10b981;">
                            <div class="viva-question" data-index="hack-${i}">
                                <span>🏆 ${q.question}</span>
                                <span class="toggle-icon">▼</span>
                            </div>
                            <div class="viva-answer" id="hack-answer-${i}">
                                <p><strong>Suggested Response:</strong></p>
                                <p>${q.suggested_response}</p>
                                ${q.key_points ? `
                                    <div style="margin-top: 0.75rem; padding: 0.75rem; background: #ecfdf5; border-radius: 6px;">
                                        <strong>Key Points:</strong>
                                        <ul style="margin-top: 0.5rem; margin-left: 1rem;">
                                            ${(Array.isArray(q.key_points) ? q.key_points : [q.key_points]).map(k => `<li>${k}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        vivaEl.innerHTML = vivaHTML;
    }

    // Pitch
    const pitchEl = document.getElementById('pitchContent');
    if (pitchEl && appState.blueprint.pitch) {
        const pitch = appState.blueprint.pitch;
        pitchEl.innerHTML = `
            <div class="pitch-box">
                <div class="pitch-label">⏱️ 30-Second Pitch</div>
                <p class="pitch-text">${pitch.thirty_second_pitch || 'Your project in 30 seconds.'}</p>
            </div>
            
            <div class="pitch-box">
                <div class="pitch-label">⏱️ 1-Minute Pitch</div>
                <p class="pitch-text">${pitch.one_minute_pitch || 'Your project in detail.'}</p>
            </div>
            
            <div class="section-card">
                <h4>🎯 Key Points to Remember</h4>
                <ul class="strength-list">
                    ${(pitch.key_points || ['Know your project well']).map(p => `<li>✓ ${p}</li>`).join('')}
                </ul>
            </div>
        `;
    }
}

/**
 * Initialize tab functionality
 */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const tocLinks = document.querySelectorAll('.toc-link');

    // Helper function to switch tabs
    function switchToTab(tabId) {
        // Update tab buttons
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));

        // Find and activate the correct tab button
        const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
        if (targetBtn) targetBtn.classList.add('active');

        // Activate the tab content
        const activeTab = document.getElementById(tabId);
        if (activeTab) activeTab.classList.add('active');

        // Update TOC links
        tocLinks.forEach(link => link.classList.remove('active'));
        const targetTocLink = document.querySelector(`.toc-link[data-tab="${tabId}"]`);
        if (targetTocLink) targetTocLink.classList.add('active');

        // Re-render Mermaid diagrams when switching to flowcharts tab
        if (tabId === 'flowcharts') {
            initMermaid();
        }
    }

    // Tab button click handlers
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            switchToTab(tabId);

            // Persist active tab for navigation
            saveBlueprintState(tabId);
        });
    });

    // TOC (sidebar) link click handlers
    tocLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = link.dataset.tab;
            switchToTab(tabId);

            // Persist active tab for navigation
            saveBlueprintState(tabId);
        });
    });
}

/**
 * Extract Mermaid block from text - bypasses Markdown entirely
 */
function extractMermaidBlock(text) {
    if (!text) return '';
    const match = text.match(/```mermaid([\s\S]*?)```/);
    return match ? match[1].trim() : text.trim();
}

/**
 * STRICT Mermaid normalizer for v11 compatibility
 * Converts to ASCII-only, removes prose, ensures valid syntax
 */
function normalizeMermaidSyntax(raw) {
    if (!raw) return '';

    return raw
        // Remove markdown fences
        .replace(/```mermaid/g, '')
        .replace(/```/g, '')
        // Normalize smart quotes & punctuation
        .replace(/[""]/g, '"')
        .replace(/['']/g, "'")
        .replace(/[–—]/g, '-')
        .replace(/[•]/g, '')
        // Remove emojis & non-ASCII (CRITICAL for v11)
        .replace(/[^\x00-\x7F]/g, '')
        // Remove numbered list prefixes
        .replace(/^\s*\d+\.\s+/gm, '')
        // Remove prose-like colons that break syntax
        .replace(/:\s+/g, ' ')
        .trim();
}

/**
 * Validate that code is actually a Mermaid flowchart
 */
function isValidMermaidFlowchart(code) {
    if (!code) return false;
    return /^(flowchart|graph)\s+(TD|LR|TB|RL|BT)\b/i.test(code.trim());
}

/**
 * Safe fallback flowchart - KNOWN VALID for Mermaid v11
 */
function getSafeFallbackFlowchart() {
    return `flowchart TD
A[User] --> B[Frontend UI]
B --> C[Backend API]
C --> D[Database]
D --> C
C --> B
B --> E[Display Result]`;
}

/**
 * Inject Mermaid diagram with validation and fallback
 * GUARANTEES a valid diagram - never shows bomb icon
 */
function injectMermaidDiagram(containerId, rawMermaidText) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Extract and normalize
    const extracted = extractMermaidBlock(rawMermaidText);
    const normalized = normalizeMermaidSyntax(extracted);

    // Use normalized code if valid, otherwise use safe fallback
    const finalMermaid = isValidMermaidFlowchart(normalized)
        ? normalized
        : getSafeFallbackFlowchart();

    // Inject raw Mermaid - NO Markdown processing
    container.innerHTML = `<div class="mermaid">
${finalMermaid}
</div>`;
}

/**
 * Initialize Mermaid diagram rendering
 */
function initMermaid() {
    if (typeof mermaid === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js';
        script.onload = () => {
            mermaid.initialize({
                startOnLoad: false,
                securityLevel: 'strict',
                theme: 'default',
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true
                }
            });
            renderMermaidDiagrams();
        };
        document.head.appendChild(script);
    } else {
        renderMermaidDiagrams();
    }
}

/**
 * Render Mermaid diagrams deterministically
 */
function renderMermaidDiagrams() {
    try {
        mermaid.run({
            querySelector: '.mermaid'
        });
    } catch (err) {
        console.error('Mermaid render failed:', err);
        // Fallback: inject safe diagram and retry
        document.querySelectorAll('.mermaid').forEach(el => {
            if (!el.querySelector('svg')) {
                el.innerHTML = getSafeFallbackFlowchart();
            }
        });
        // Retry render with safe content
        try {
            mermaid.run({ querySelector: '.mermaid' });
        } catch (e) {
            console.error('Mermaid fallback also failed:', e);
        }
    }
}

/**
 * Escape HTML for safe display
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Download diagram as SVG
 */
function downloadDiagramAsSVG(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const svg = container.querySelector('svg');
    if (!svg) {
        alert('Diagram not available for download');
        return;
    }

    const svgData = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${containerId}_diagram.svg`;
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * Download diagram as PNG
 */
function downloadDiagramAsPNG(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const svg = container.querySelector('svg');
    if (!svg) {
        alert('Diagram not available for download');
        return;
    }

    // Get SVG dimensions
    const svgRect = svg.getBoundingClientRect();
    const canvas = document.createElement('canvas');
    const scale = 2; // Higher resolution
    canvas.width = svgRect.width * scale;
    canvas.height = svgRect.height * scale;

    const ctx = canvas.getContext('2d');
    ctx.scale(scale, scale);
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const svgData = new XMLSerializer().serializeToString(svg);
    const img = new Image();

    img.onload = () => {
        ctx.drawImage(img, 0, 0);
        const pngUrl = canvas.toDataURL('image/png');

        const a = document.createElement('a');
        a.href = pngUrl;
        a.download = `${containerId}_diagram.png`;
        a.click();
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
}

// Make download functions globally available
window.downloadDiagramAsSVG = downloadDiagramAsSVG;
window.downloadDiagramAsPNG = downloadDiagramAsPNG;

/**
 * Initialize viva Q&A toggle functionality with keyboard accessibility
 */
function initVivaToggles() {
    document.querySelectorAll('.viva-question').forEach(q => {
        // Make focusable for keyboard navigation
        q.setAttribute('tabindex', '0');
        q.setAttribute('role', 'button');

        const toggleAnswer = () => {
            const index = q.dataset.index;
            // Handle both regular viva and hackathon question IDs
            let answer = document.getElementById(`answer-${index}`);
            if (!answer) {
                answer = document.getElementById(`hack-answer-${index?.replace('hack-', '')}`);
            }
            const icon = q.querySelector('.toggle-icon');

            if (answer) {
                const isVisible = answer.classList.toggle('visible');
                if (icon) {
                    icon.classList.toggle('rotated', isVisible);
                }
                // Update ARIA state
                q.setAttribute('aria-expanded', isVisible);
            }
        };

        // Click handler
        q.addEventListener('click', toggleAnswer);

        // Keyboard handler (Enter and Space)
        q.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleAnswer();
            }
        });
    });
}

// ==========================================================
// MODAL HANDLING
// ==========================================================

/**
 * Initialize modal functionality
 */
function initModals() {
    const howItWorksBtn = document.getElementById('howItWorksBtn');
    const modal = document.getElementById('howItWorksModal');
    const closeBtn = document.getElementById('closeModal');

    if (howItWorksBtn && modal) {
        howItWorksBtn.addEventListener('click', (e) => {
            e.preventDefault();
            modal.classList.remove('hidden');
        });
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
        });
    }

    // Close modal when clicking outside
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    }
}

// ==========================================================
// EXPORT FUNCTIONALITY
// ==========================================================

/**
 * Export blueprint as JSON
 */
function exportJSON() {
    const data = {
        projectTitle: appState.blueprint.projectTitle,
        generatedAt: new Date().toISOString(),
        idea: appState.rawIdea,
        expandedIdea: appState.expandedIdea,
        evaluation: appState.blueprint.evaluation,
        systemFlow: appState.blueprint.systemFlow,
        techStack: appState.blueprint.techStack,
        vivaGuide: appState.blueprint.vivaGuide,
        pitch: appState.blueprint.pitch,
        flowcharts: {
            userFlow: appState.blueprint.userFlowMermaid,
            techStack: appState.blueprint.techStackMermaid
        }
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${appState.blueprint.projectTitle || 'project'}_blueprint.json`;
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * Export dashboard as a proper PDF document using jsPDF
 * Creates a complete document with all sections
 */
async function exportAsPDF() {
    // Check if jsPDF is available
    if (typeof jspdf === 'undefined' || typeof html2canvas === 'undefined') {
        alert('PDF export libraries are loading. Please try again in a moment.');
        return;
    }

    const { jsPDF } = jspdf;
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 15;
    const contentWidth = pageWidth - (margin * 2);
    let yPosition = margin;

    // Helper to add page break if needed
    const checkPageBreak = (neededHeight) => {
        if (yPosition + neededHeight > pageHeight - margin) {
            pdf.addPage();
            yPosition = margin;
            return true;
        }
        return false;
    };

    // Helper to normalize text for PDF (Unicode-safe)
    const normalizeTextForPDF = (text) => {
        if (!text) return '';
        return String(text)
            .replace(/[•●○◦▪▸►▶]/g, '-')
            .replace(/[""„‟]/g, '"')
            .replace(/[''‚‛]/g, "'")
            .replace(/[–—―]/g, '-')
            .replace(/[…]/g, '...')
            .replace(/[™®©]/g, '')
            .replace(/[✓✔☑]/g, '[x]')
            .replace(/[✗✘☐]/g, '[ ]')
            .replace(/[★☆⭐]/g, '*')
            .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
            .replace(/[^\x00-\x7F]/g, '');
    };

    // Helper to add section
    const addSection = (title, content) => {
        checkPageBreak(30);

        // Section title - normalize for PDF
        const cleanTitle = normalizeTextForPDF(title);
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(79, 70, 229);
        pdf.text(cleanTitle, margin, yPosition);
        yPosition += 8;

        // Section content - normalize for PDF
        const cleanContent = normalizeTextForPDF(content);
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        pdf.setTextColor(0, 0, 0);

        const lines = pdf.splitTextToSize(cleanContent, contentWidth);
        lines.forEach(line => {
            checkPageBreak(6);
            pdf.text(line, margin, yPosition);
            yPosition += 5;
        });

        yPosition += 10;
    };

    // ========== TITLE PAGE ==========
    pdf.setFontSize(24);
    pdf.setFont('helvetica', 'bold');
    pdf.setTextColor(79, 70, 229);
    const title = appState.blueprint.projectTitle || 'Project Blueprint';
    pdf.text(title, pageWidth / 2, 60, { align: 'center' });

    pdf.setFontSize(12);
    pdf.setFont('helvetica', 'normal');
    pdf.setTextColor(100, 100, 100);
    pdf.text('Generated by BlueprintAI', pageWidth / 2, 75, { align: 'center' });
    pdf.text(new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }), pageWidth / 2, 85, { align: 'center' });

    // Add a line separator
    pdf.setDrawColor(79, 70, 229);
    pdf.line(margin, 100, pageWidth - margin, 100);

    // Table of contents preview
    yPosition = 120;
    pdf.setFontSize(14);
    pdf.setFont('helvetica', 'bold');
    pdf.setTextColor(0, 0, 0);
    pdf.text('Document Contents:', margin, yPosition);
    yPosition += 10;

    const sections = [
        'Problem Definition',
        'Features',
        'Feasibility Analysis',
        'System Flow',
        'Technology Stack',
        'Comparison & Uniqueness',
        'Viva & Hackathon Preparation',
        'Project Pitch'
    ];

    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    sections.forEach(section => {
        pdf.text(`• ${section}`, margin + 5, yPosition);
        yPosition += 6;
    });

    // ========== CONTENT PAGES ==========
    pdf.addPage();
    yPosition = margin;

    // 1. Problem Definition
    if (appState.expandedIdea) {
        addSection('📋 Problem Definition',
            `Problem Statement:\n${appState.expandedIdea.problem_statement || appState.rawIdea}\n\n` +
            `Target Users: ${Array.isArray(appState.expandedIdea.target_users) ? appState.expandedIdea.target_users.join(', ') : (appState.expandedIdea.target_users || 'Not specified')}\n\n` +
            `Objectives: ${Array.isArray(appState.expandedIdea.objectives) ? appState.expandedIdea.objectives.join('; ') : 'Not specified'}`
        );
    }

    // 2. Features
    if (appState.blueprint.featuresDetailed?.features) {
        const featuresText = appState.blueprint.featuresDetailed.features
            .map(f => `• ${f.feature_name}: ${f.what_it_does}`)
            .join('\n');
        addSection('✨ Project Features', featuresText);
    }

    // 3. Feasibility
    if (appState.blueprint.evaluation) {
        const eval_ = appState.blueprint.evaluation;
        addSection('📊 Feasibility Analysis',
            `Feasibility Level: ${eval_.feasibility_level || 'Medium'}\n\n` +
            `${eval_.feasibility_explanation || ''}\n\n` +
            `Strengths:\n${(eval_.strengths || []).map(s => `• ${s}`).join('\n')}\n\n` +
            `Risks:\n${(eval_.risks || []).map(r => `• ${r}`).join('\n')}`
        );
    }

    // 4. System Flow
    if (appState.blueprint.systemFlow) {
        const flow = appState.blueprint.systemFlow;
        const stepsText = (flow.steps || [])
            .map(s => `${s.step_number}. ${s.actor}: ${s.action}`)
            .join('\n');
        addSection('🔄 System Flow',
            `${flow.flow_title || 'System Flow'}\n\n${stepsText}\n\n${flow.summary || ''}`
        );
    }

    // 5. Tech Stack
    if (appState.blueprint.techStack) {
        const techText = appState.blueprint.techStack
            .map(t => `• ${t.technology} (${t.category}): ${t.justification}`)
            .join('\n');
        addSection('🛠️ Technology Stack', techText);
    }

    // 6. Comparison
    if (appState.blueprint.comparison) {
        const comp = appState.blueprint.comparison;
        const existingText = (comp.existing_solutions || [])
            .map(s => `• ${s.solution_name}: ${s.what_it_does}`)
            .join('\n');
        addSection('🔍 Comparison & Uniqueness',
            `Existing Solutions:\n${existingText}\n\n` +
            `What Makes This Project Unique:\n${(comp.unique_aspects || []).map(u => `• ${u}`).join('\n')}\n\n` +
            `${comp.summary_insight || ''}`
        );
    }

    // 7. Viva Guide
    if (appState.blueprint.vivaGuide) {
        const viva = appState.blueprint.vivaGuide;
        const qaText = (viva.common_questions || [])
            .slice(0, 5)
            .map(q => `Q: ${q.question}\nA: ${q.suggested_answer}`)
            .join('\n\n');
        addSection('🎓 Viva Preparation',
            `Project Overview:\n${viva.project_overview_explanation || ''}\n\n` +
            `Common Questions:\n${qaText}`
        );
    }

    // 8. Pitch
    if (appState.blueprint.pitch) {
        const pitch = appState.blueprint.pitch;
        addSection('🎤 Project Pitch',
            `30-Second Pitch:\n${pitch.thirty_second_pitch || ''}\n\n` +
            `1-Minute Pitch:\n${pitch.one_minute_pitch || ''}\n\n` +
            `Key Points:\n${(pitch.key_points || []).map(p => `• ${p}`).join('\n')}`
        );
    }

    // NOTE: Footer removed per requirements to prevent artifacts

    // Save the PDF
    const filename = `${(appState.blueprint.projectTitle || 'project').replace(/[^a-z0-9]/gi, '_')}_blueprint.pdf`;
    pdf.save(filename);

    console.log('📄 PDF exported successfully');
}

// Keep printDashboard as alias for backward compatibility
function printDashboard() {
    exportAsPDF();
}

// ==========================================================
// INITIALIZATION
// ==========================================================

/**
 * Initialize the application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize based on current page
    initIdeaForm();
    initChatPage();
    initTabs();      // Initialize tab/TOC navigation
    initModals();

    // Set up export buttons
    const exportJsonBtn = document.getElementById('exportJsonBtn');
    const exportPdfBtn = document.getElementById('exportPdfBtn');
    const startOverBtn = document.getElementById('startOverBtn');

    if (exportJsonBtn) exportJsonBtn.addEventListener('click', exportJSON);
    if (exportPdfBtn) exportPdfBtn.addEventListener('click', printDashboard);
    if (startOverBtn) startOverBtn.addEventListener('click', clearState);
});

// Make functions available globally for onclick handlers
window.exportJSON = exportJSON;
window.printDashboard = printDashboard;
window.exportAsPDF = exportAsPDF;
window.clearState = clearState;
window.startOver = startOver;

// ==========================================================
// COPY-TO-CLIPBOARD FUNCTIONALITY
// ==========================================================

/**
 * Copy the text content of a blueprint section to clipboard
 * Shows "Copied!" feedback for 1.5 seconds
 * 
 * @param {string} sectionId - The ID of the section content element
 * @param {HTMLElement} button - The copy button element
 */
async function copySectionToClipboard(sectionId, button) {
    const sectionElement = document.getElementById(sectionId);

    if (!sectionElement) {
        console.warn(`Section ${sectionId} not found`);
        return;
    }

    // Get text content only (strips HTML)
    const textContent = sectionElement.innerText || sectionElement.textContent;

    try {
        await navigator.clipboard.writeText(textContent);

        // Show feedback
        button.classList.add('copied');

        // Remove feedback after 1.5 seconds
        setTimeout(() => {
            button.classList.remove('copied');
        }, 1500);

    } catch (err) {
        console.error('Failed to copy:', err);
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = textContent;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);

        // Show feedback
        button.classList.add('copied');
        setTimeout(() => {
            button.classList.remove('copied');
        }, 1500);
    }
}

/**
 * Initialize copy buttons on the dashboard page
 */
function initCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');

    copyButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = button.getAttribute('data-section');
            copySectionToClipboard(sectionId, button);
        });
    });
}

// Initialize copy buttons when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initCopyButtons();
    initChatPage();
    initDashboard();
    initDashboardChangeRequest();
});

/**
 * Initialize chat page functionality
 */
function initChatPage() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const finalizeBtn = document.getElementById('finalizeBtn');
    const chatMessagesEl = document.getElementById('chatMessages');

    // Not on chat page
    if (!chatInput) return;

    // Load existing messages
    loadState();
    renderChatMessages();
    updateDraftSummaryDisplay();

    // Start session if no messages yet
    if (appState.chatMessages.length === 0 && appState.rawIdea) {
        startChatSession();
    }

    // Send button click
    if (sendBtn) {
        sendBtn.addEventListener('click', async () => {
            const message = chatInput.value.trim();
            if (!message) return;

            chatInput.value = '';
            chatInput.disabled = true;
            sendBtn.disabled = true;

            const result = await sendChatMessage(message);

            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();

            renderChatMessages();
            updateDraftSummaryDisplay();
        });
    }

    // Enter key to send
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendBtn?.click();
            }
        });
    }

    // Finalize button
    if (finalizeBtn) {
        finalizeBtn.addEventListener('click', async () => {
            if (!appState.draftSummary) {
                alert('Please chat a bit more to define your project before generating the blueprint.');
                return;
            }

            finalizeBtn.disabled = true;
            finalizeBtn.textContent = 'Generating Blueprint...';

            // Lock the draft
            if (transitionToFinalized()) {
                // Generate the full blueprint
                await generateFullBlueprint();
            } else {
                finalizeBtn.disabled = false;
                finalizeBtn.textContent = '✨ Finalize Idea & Generate Blueprint';
                alert('Please continue chatting to clarify your idea first.');
            }
        });
    }
}

/**
 * Render chat messages with WhatsApp-style bubbles
 */
function renderChatMessages() {
    const chatMessagesEl = document.getElementById('chatMessages');
    if (!chatMessagesEl) return;

    chatMessagesEl.innerHTML = appState.chatMessages.map(msg => `
        <div class="chat-bubble ${msg.role === 'ai' ? 'ai' : 'user'}">
            ${msg.content || ''}
        </div>
    `).join('');

    // Scroll to bottom
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

/**
 * Update draft summary display in sidebar
 */
function updateDraftSummaryDisplay() {
    const draftEl = document.getElementById('draftSummaryContent');
    if (!draftEl || !appState.draftSummary) return;

    const draft = appState.draftSummary;
    draftEl.innerHTML = `
        <p><strong>Problem:</strong> ${draft.problem_statement || 'Not defined yet'}</p>
        ${draft.target_users ? `<p><strong>Users:</strong> ${draft.target_users}</p>` : ''}
        ${draft.main_features?.length > 0 ? `
            <p><strong>Features:</strong></p>
            <ul style="margin-left: 1rem; font-size: 0.85rem;">
                ${draft.main_features.map(f => `<li>${f}</li>`).join('')}
            </ul>
        ` : ''}
    `;
}

/**
 * Initialize change request functionality on dashboard
 */
function initDashboardChangeRequest() {
    const changeInput = document.getElementById('changeRequestInput');
    const changeBtn = document.getElementById('applyChangeBtn');

    if (!changeBtn || !changeInput) return;

    changeBtn.addEventListener('click', async () => {
        const request = changeInput.value.trim();
        if (!request) {
            alert('Please describe what you want to change.');
            return;
        }

        changeBtn.disabled = true;
        changeBtn.textContent = 'Applying changes...';

        const result = await applyChangeRequest(request);

        if (result.success) {
            changeInput.value = '';
            alert(`Change applied: ${result.data.change_description}\n\nThe following sections may need regeneration:\n${result.data.sections_to_regenerate.join(', ')}`);
            // Optionally refresh the dashboard sections here
        } else {
            alert('Failed to apply change: ' + result.error);
        }

        changeBtn.disabled = false;
        changeBtn.textContent = 'Apply Change';
    });
}
