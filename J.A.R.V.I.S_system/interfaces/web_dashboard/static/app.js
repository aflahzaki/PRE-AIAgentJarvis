/**
 * J.A.R.V.I.S Web Dashboard - Frontend Application
 *
 * Vanilla JavaScript SPA handling navigation, API calls,
 * and dynamic content rendering for all dashboard sections.
 */

(function () {
    'use strict';

    // ============================================
    // API Wrapper
    // ============================================

    const API_BASE = '/api';

    async function apiFetch(endpoint, options = {}) {
        const url = API_BASE + endpoint;
        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed with status ' + response.status);
            }

            return data;
        } catch (error) {
            console.error('API Error:', endpoint, error);
            throw error;
        }
    }

    // ============================================
    // Router - Section Navigation
    // ============================================

    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');

    function navigateTo(sectionId) {
        // Hide all sections
        sections.forEach(function (sec) {
            sec.classList.remove('active');
        });

        // Deactivate all nav items
        navItems.forEach(function (item) {
            item.classList.remove('active');
        });

        // Show target section
        var target = document.getElementById('section-' + sectionId);
        if (target) {
            target.classList.add('active');
        }

        // Activate nav item
        var navItem = document.querySelector('.nav-item[data-section="' + sectionId + '"]');
        if (navItem) {
            navItem.classList.add('active');
        }

        // Load data for the section
        loadSectionData(sectionId);
    }

    navItems.forEach(function (item) {
        item.addEventListener('click', function () {
            var section = this.getAttribute('data-section');
            navigateTo(section);
        });
    });

    function loadSectionData(section) {
        switch (section) {
            case 'tasks':
                loadTasks();
                break;
            case 'knowledge':
                loadKnowledge();
                break;
            case 'journal':
                loadJournals();
                break;
            case 'habits':
                loadHabits();
                break;
            case 'status':
                loadStatus();
                break;
        }
    }

    // ============================================
    // Chat Section
    // ============================================

    var chatForm = document.getElementById('chat-form');
    var chatInput = document.getElementById('chat-input');
    var chatMessages = document.getElementById('chat-messages');
    var typingIndicator = document.getElementById('typing-indicator');

    chatForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        var message = chatInput.value.trim();
        if (!message) return;

        // Add user message
        appendMessage('user', message);
        chatInput.value = '';

        // Show typing indicator
        typingIndicator.style.display = 'flex';
        scrollChatToBottom();

        try {
            var data = await apiFetch('/chat', {
                method: 'POST',
                body: JSON.stringify({ message: message }),
            });

            typingIndicator.style.display = 'none';

            var meta = '';
            if (data.model) {
                meta = data.provider + ' / ' + data.model;
                if (data.task_type) meta += ' [' + data.task_type + ']';
            }

            appendMessage('assistant', data.response, meta);
        } catch (error) {
            typingIndicator.style.display = 'none';
            appendMessage('assistant', 'Error: ' + error.message);
        }
    });

    function appendMessage(role, content, meta) {
        var div = document.createElement('div');
        div.className = 'message ' + role;

        var avatar = role === 'assistant' ? 'J' : 'U';
        var html = '<div class="message-avatar">' + avatar + '</div>';
        html += '<div class="message-content">';
        html += '<p>' + escapeHtml(content) + '</p>';
        if (meta) {
            html += '<div class="message-meta">' + escapeHtml(meta) + '</div>';
        }
        html += '</div>';

        div.innerHTML = html;
        chatMessages.appendChild(div);
        scrollChatToBottom();
    }

    function scrollChatToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // ============================================
    // Tasks Section
    // ============================================

    var taskForm = document.getElementById('task-form');
    var taskFilterStatus = document.getElementById('task-filter-status');
    var taskFilterCategory = document.getElementById('task-filter-category');

    document.getElementById('btn-add-task').addEventListener('click', toggleTaskForm);

    taskFilterStatus.addEventListener('change', loadTasks);
    taskFilterCategory.addEventListener('change', loadTasks);

    taskForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        var title = document.getElementById('task-title').value.trim();
        if (!title) return;

        var body = {
            title: title,
            description: document.getElementById('task-description').value.trim() || null,
            priority: document.getElementById('task-priority').value,
            category: document.getElementById('task-category').value.trim() || null,
            due_date: document.getElementById('task-due-date').value || null,
        };

        try {
            await apiFetch('/tasks', {
                method: 'POST',
                body: JSON.stringify(body),
            });
            taskForm.reset();
            toggleTaskForm();
            loadTasks();
        } catch (error) {
            alert('Error creating task: ' + error.message);
        }
    });

    async function loadTasks() {
        var container = document.getElementById('tasks-list');
        var status = taskFilterStatus.value;
        var category = taskFilterCategory.value;

        var query = '';
        if (status) query += '?status=' + encodeURIComponent(status);
        if (category) query += (query ? '&' : '?') + 'category=' + encodeURIComponent(category);

        try {
            var data = await apiFetch('/tasks' + query);
            var tasks = data.tasks || [];

            if (tasks.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No tasks found.</p></div>';
                return;
            }

            var html = '';
            tasks.forEach(function (task) {
                html += renderTaskCard(task);
            });
            container.innerHTML = html;

            // Attach event handlers for task actions
            container.querySelectorAll('.task-complete-btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    completeTask(this.getAttribute('data-id'));
                });
            });
            container.querySelectorAll('.task-delete-btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    deleteTask(this.getAttribute('data-id'));
                });
            });
        } catch (error) {
            container.innerHTML = '<div class="empty-state"><p>Error loading tasks: ' + escapeHtml(error.message) + '</p></div>';
        }
    }

    function renderTaskCard(task) {
        var statusBadge = '<span class="badge badge-' + task.status + '">' + task.status + '</span>';
        var priorityBadge = '<span class="badge badge-' + task.priority + '">' + task.priority + '</span>';

        var html = '<div class="item-card">';
        html += '<div class="item-info">';
        html += '<div class="item-title">' + escapeHtml(task.title) + '</div>';
        if (task.description) {
            html += '<div class="item-description">' + escapeHtml(task.description) + '</div>';
        }
        html += '<div class="item-meta">' + statusBadge + ' ' + priorityBadge;
        if (task.category) html += ' <span>' + escapeHtml(task.category) + '</span>';
        if (task.due_date) html += ' <span>Due: ' + task.due_date.split('T')[0] + '</span>';
        html += '</div></div>';
        html += '<div class="item-actions">';
        if (task.status !== 'completed') {
            html += '<button class="btn-success task-complete-btn" data-id="' + task.id + '">Done</button>';
        }
        html += '<button class="btn-danger task-delete-btn" data-id="' + task.id + '">Delete</button>';
        html += '</div></div>';
        return html;
    }

    async function completeTask(taskId) {
        try {
            await apiFetch('/tasks/' + taskId, {
                method: 'PUT',
                body: JSON.stringify({ status: 'completed' }),
            });
            loadTasks();
        } catch (error) {
            alert('Error completing task: ' + error.message);
        }
    }

    async function deleteTask(taskId) {
        if (!confirm('Delete this task?')) return;
        try {
            await apiFetch('/tasks/' + taskId, { method: 'DELETE' });
            loadTasks();
        } catch (error) {
            alert('Error deleting task: ' + error.message);
        }
    }

    // ============================================
    // Knowledge Section
    // ============================================

    var knowledgeForm = document.getElementById('knowledge-form');
    var knowledgeSearch = document.getElementById('knowledge-search');

    document.getElementById('btn-add-knowledge').addEventListener('click', toggleKnowledgeForm);
    document.getElementById('btn-search-knowledge').addEventListener('click', searchKnowledge);

    knowledgeSearch.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') searchKnowledge();
    });

    knowledgeForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        var title = document.getElementById('knowledge-title').value.trim();
        var content = document.getElementById('knowledge-content').value.trim();
        if (!title || !content) return;

        var body = {
            title: title,
            content: content,
            category: document.getElementById('knowledge-category').value.trim() || null,
            tags: document.getElementById('knowledge-tags').value.trim() || null,
            source: document.getElementById('knowledge-source').value.trim() || null,
        };

        try {
            await apiFetch('/knowledge', {
                method: 'POST',
                body: JSON.stringify(body),
            });
            knowledgeForm.reset();
            toggleKnowledgeForm();
            loadKnowledge();
        } catch (error) {
            alert('Error adding knowledge: ' + error.message);
        }
    });

    async function loadKnowledge() {
        var container = document.getElementById('knowledge-list');
        try {
            var data = await apiFetch('/knowledge');
            var items = data.knowledge || [];

            if (items.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No knowledge entries yet.</p></div>';
                return;
            }

            var html = '';
            items.forEach(function (item) {
                html += renderKnowledgeCard(item);
            });
            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = '<div class="empty-state"><p>Error loading knowledge: ' + escapeHtml(error.message) + '</p></div>';
        }
    }

    async function searchKnowledge() {
        var query = knowledgeSearch.value.trim();
        if (!query) {
            loadKnowledge();
            return;
        }

        var container = document.getElementById('knowledge-list');
        try {
            var data = await apiFetch('/knowledge/search?q=' + encodeURIComponent(query));
            var items = data.results || [];

            if (items.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No results for "' + escapeHtml(query) + '"</p></div>';
                return;
            }

            var html = '';
            items.forEach(function (item) {
                html += renderKnowledgeCard(item);
            });
            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = '<div class="empty-state"><p>Search error: ' + escapeHtml(error.message) + '</p></div>';
        }
    }

    function renderKnowledgeCard(item) {
        var html = '<div class="item-card">';
        html += '<div class="item-info">';
        html += '<div class="item-title">' + escapeHtml(item.title) + '</div>';
        if (item.content) {
            var preview = item.content.length > 200 ? item.content.substring(0, 200) + '...' : item.content;
            html += '<div class="item-description">' + escapeHtml(preview) + '</div>';
        }
        html += '<div class="item-meta">';
        if (item.category) html += '<span class="badge badge-medium">' + escapeHtml(item.category) + '</span>';
        if (item.tags) html += '<span>' + escapeHtml(item.tags) + '</span>';
        if (item.source) html += '<span>' + escapeHtml(item.source) + '</span>';
        html += '</div></div></div>';
        return html;
    }

    // ============================================
    // Journal Section
    // ============================================

    var journalForm = document.getElementById('journal-form');

    // Set default date to today
    document.getElementById('journal-date').value = new Date().toISOString().split('T')[0];

    journalForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        var content = document.getElementById('journal-content').value.trim();
        if (!content) return;

        var body = {
            date: document.getElementById('journal-date').value,
            mood: document.getElementById('journal-mood').value || null,
            content: content,
            highlights: document.getElementById('journal-highlights').value.trim() || null,
            challenges: document.getElementById('journal-challenges').value.trim() || null,
            tomorrow_plan: document.getElementById('journal-tomorrow').value.trim() || null,
        };

        try {
            await apiFetch('/journals', {
                method: 'POST',
                body: JSON.stringify(body),
            });
            journalForm.reset();
            document.getElementById('journal-date').value = new Date().toISOString().split('T')[0];
            loadJournals();
        } catch (error) {
            alert('Error saving journal: ' + error.message);
        }
    });

    async function loadJournals() {
        var container = document.getElementById('journals-list');
        try {
            var data = await apiFetch('/journals');
            var journals = data.journals || [];

            if (journals.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No journal entries yet. Start writing!</p></div>';
                return;
            }

            var html = '';
            journals.forEach(function (journal) {
                html += renderJournalCard(journal);
            });
            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = '<div class="empty-state"><p>Error loading journals: ' + escapeHtml(error.message) + '</p></div>';
        }
    }

    function renderJournalCard(journal) {
        var moodClass = journal.mood ? 'mood-' + journal.mood : '';
        var html = '<div class="item-card">';
        html += '<div class="item-info">';
        html += '<div class="item-title">' + (journal.date || 'Unknown date');
        if (journal.mood) {
            html += ' <span class="' + moodClass + '">(' + journal.mood + ')</span>';
        }
        html += '</div>';
        html += '<div class="item-description">' + escapeHtml(journal.content) + '</div>';
        html += '<div class="item-meta">';
        if (journal.highlights) html += '<span>Highlights: ' + escapeHtml(journal.highlights.substring(0, 50)) + '</span>';
        if (journal.challenges) html += '<span>Challenges: ' + escapeHtml(journal.challenges.substring(0, 50)) + '</span>';
        html += '</div></div></div>';
        return html;
    }

    // ============================================
    // Habits Section
    // ============================================

    var habitForm = document.getElementById('habit-form');

    document.getElementById('btn-add-habit').addEventListener('click', toggleHabitForm);

    habitForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        var name = document.getElementById('habit-name').value.trim();
        if (!name) return;

        var body = {
            name: name,
            frequency: document.getElementById('habit-frequency').value,
            target_count: parseInt(document.getElementById('habit-target').value) || 1,
        };

        try {
            await apiFetch('/habits', {
                method: 'POST',
                body: JSON.stringify(body),
            });
            habitForm.reset();
            toggleHabitForm();
            loadHabits();
        } catch (error) {
            alert('Error creating habit: ' + error.message);
        }
    });

    async function loadHabits() {
        var container = document.getElementById('habits-list');
        try {
            var data = await apiFetch('/habits');
            var habits = data.habits || [];

            if (habits.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No habits tracked yet. Create one!</p></div>';
                return;
            }

            var html = '';
            habits.forEach(function (habit) {
                html += renderHabitCard(habit);
            });
            container.innerHTML = html;

            // Attach log buttons
            container.querySelectorAll('.habit-log-btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    logHabit(this.getAttribute('data-id'));
                });
            });
        } catch (error) {
            container.innerHTML = '<div class="empty-state"><p>Error loading habits: ' + escapeHtml(error.message) + '</p></div>';
        }
    }

    function renderHabitCard(habit) {
        var today = new Date().toISOString().split('T')[0];
        var loggedToday = false;
        var logs = habit.recent_logs || [];

        logs.forEach(function (log) {
            if (log.logged_date === today) loggedToday = true;
        });

        var html = '<div class="habit-card">';
        html += '<div class="habit-header">';
        html += '<span class="habit-name">' + escapeHtml(habit.name) + '</span>';
        html += '<span class="habit-freq">' + habit.frequency + ' (target: ' + habit.target_count + ')</span>';
        html += '</div>';

        // Show recent log dots (last 7 days)
        html += '<div class="habit-logs">';
        for (var i = 6; i >= 0; i--) {
            var d = new Date();
            d.setDate(d.getDate() - i);
            var dateStr = d.toISOString().split('T')[0];
            var completed = logs.some(function (log) { return log.logged_date === dateStr; });
            var dayLabel = d.toLocaleDateString('en', { weekday: 'narrow' });
            html += '<div class="habit-log-dot' + (completed ? ' completed' : '') + '" title="' + dateStr + '">' + dayLabel + '</div>';
        }
        html += '</div>';

        html += '<div class="habit-actions">';
        if (!loggedToday) {
            html += '<button class="btn-success habit-log-btn" data-id="' + habit.id + '">Log Today</button>';
        } else {
            html += '<span class="badge badge-completed">Done today!</span>';
        }
        html += '</div></div>';
        return html;
    }

    async function logHabit(habitId) {
        try {
            await apiFetch('/habits/' + habitId + '/log', {
                method: 'POST',
                body: JSON.stringify({ count: 1 }),
            });
            loadHabits();
        } catch (error) {
            alert('Error logging habit: ' + error.message);
        }
    }

    // ============================================
    // Status Section
    // ============================================

    async function loadStatus() {
        var container = document.getElementById('status-panel');
        try {
            var data = await apiFetch('/status');
            var html = '';

            // System info card
            html += '<div class="status-card">';
            html += '<div class="status-card-title">System</div>';
            html += '<div class="status-item"><span class="status-label">Name</span><span class="status-value">' + (data.system || 'J.A.R.V.I.S') + '</span></div>';
            html += '<div class="status-item"><span class="status-label">Version</span><span class="status-value">' + (data.version || '2.0.0') + '</span></div>';
            html += '</div>';

            // Database card
            if (data.database) {
                html += '<div class="status-card">';
                html += '<div class="status-card-title">Database</div>';
                var dbOk = data.database.success;
                html += '<div class="status-item"><span class="status-label">Status</span><span class="status-value ' + (dbOk ? 'online' : 'offline') + '">' + (dbOk ? 'Connected' : 'Disconnected') + '</span></div>';
                if (data.database.db_type) {
                    html += '<div class="status-item"><span class="status-label">Type</span><span class="status-value">' + data.database.db_type + '</span></div>';
                }
                if (data.database.error) {
                    html += '<div class="status-item"><span class="status-label">Error</span><span class="status-value offline">' + escapeHtml(data.database.error) + '</span></div>';
                }
                html += '</div>';
            }

            // Orchestrator card
            if (data.orchestrator) {
                html += '<div class="status-card">';
                html += '<div class="status-card-title">Orchestrator</div>';
                if (data.orchestrator.error) {
                    html += '<div class="status-item"><span class="status-label">Status</span><span class="status-value offline">' + escapeHtml(data.orchestrator.error) + '</span></div>';
                } else {
                    // Providers
                    if (data.orchestrator.providers) {
                        var providers = data.orchestrator.providers;
                        Object.keys(providers).forEach(function (key) {
                            var val = providers[key];
                            var statusStr = typeof val === 'object' ? JSON.stringify(val) : String(val);
                            html += '<div class="status-item"><span class="status-label">' + escapeHtml(key) + '</span><span class="status-value">' + escapeHtml(statusStr) + '</span></div>';
                        });
                    }
                    // Memory
                    if (data.orchestrator.memory) {
                        var memory = data.orchestrator.memory;
                        Object.keys(memory).forEach(function (key) {
                            html += '<div class="status-item"><span class="status-label">' + escapeHtml(key) + '</span><span class="status-value">' + escapeHtml(String(memory[key])) + '</span></div>';
                        });
                    }
                }
                html += '</div>';
            }

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = '<div class="status-card"><div class="status-card-title">Error</div><p>' + escapeHtml(error.message) + '</p></div>';
        }
    }

    // ============================================
    // Toggle Functions (global for inline onclick)
    // ============================================

    window.toggleTaskForm = function () {
        var container = document.getElementById('task-form-container');
        container.style.display = container.style.display === 'none' ? 'block' : 'none';
    };

    window.toggleKnowledgeForm = function () {
        var container = document.getElementById('knowledge-form-container');
        container.style.display = container.style.display === 'none' ? 'block' : 'none';
    };

    window.toggleHabitForm = function () {
        var container = document.getElementById('habit-form-container');
        container.style.display = container.style.display === 'none' ? 'block' : 'none';
    };

    // ============================================
    // Utilities
    // ============================================

    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ============================================
    // Initialization
    // ============================================

    // Chat section is active by default, no data load needed on start

})();
