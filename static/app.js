// app.js - Frontend Logic for Kanban Board

const API_BASE = '/api/tasks/';
let tasks = [];
let ws = null;

// DOM Elements
const board = document.getElementById('board');
const btnAddTask = document.getElementById('btn-add-task');
const taskModal = document.getElementById('task-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const btnCancel = document.getElementById('btn-cancel');
const taskForm = document.getElementById('task-form');
const filterUser = document.getElementById('filter-user');
const filterMonth = document.getElementById('filter-month');
const connectionStatus = document.getElementById('connection-status');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchTasks();
    setupWebSockets();
    setupDragAndDrop();
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    btnAddTask.addEventListener('click', () => openModal());
    btnCloseModal.addEventListener('click', closeModal);
    btnCancel.addEventListener('click', closeModal);
    taskForm.addEventListener('submit', handleTaskSubmit);
    
    filterUser.addEventListener('change', renderTasks);
    filterMonth.addEventListener('change', renderTasks);
}

// Fetch initial tasks from REST API
async function fetchTasks() {
    try {
        const response = await fetch(API_BASE);
        if (response.ok) {
            tasks = await response.json();
            renderTasks();
        } else {
            console.error('Failed to fetch tasks');
        }
    } catch (error) {
        console.error('Error fetching tasks:', error);
    }
}

// Render Tasks to DOM
function renderTasks() {
    // Clear columns
    document.querySelectorAll('.bcol-body').forEach(col => col.innerHTML = '');
    
    const userF = filterUser.value;
    const monthF = filterMonth.value;
    
    let counts = { week: 0, month: 0, review: 0, done: 0 };
    
    tasks.forEach(task => {
        // Apply filters
        if (userF !== 'Todos' && task.user !== userF) return;
        if (monthF !== 'Todos' && task.month_filter !== monthF) return;
        
        // Count and append
        if (counts[task.bucket] !== undefined) {
            counts[task.bucket]++;
            const col = document.getElementById(`col-${task.bucket}`);
            if (col) {
                col.appendChild(createTaskElement(task));
            }
        }
    });
    
    // Update counts
    document.getElementById('count-week').textContent = counts.week;
    document.getElementById('count-month').textContent = counts.month;
    document.getElementById('count-review').textContent = counts.review;
    document.getElementById('count-done').textContent = counts.done;
}

// Create Task DOM Element
function createTaskElement(task) {
    const el = document.createElement('div');
    el.className = `task-card priority-${task.priority}`;
    el.draggable = true;
    el.dataset.id = task.id;
    
    let dueBadge = task.due_date ? `<span class="badge" style="background: rgba(255,255,255,0.1); color: #fff;">⏰ ${task.due_date}</span>` : '';

    let badgesHTML = `
        <span class="badge badge-user">👤 ${task.user}</span>
        <span class="badge badge-priority-${task.priority.toLowerCase()}">🔥 ${task.priority}</span>
        <span class="badge badge-month">📅 ${task.month_filter}</span>
        ${dueBadge}
    `;

    el.innerHTML = `
        <div class="task-header">
            <div class="task-title">${task.title}</div>
        </div>
        ${task.description ? `<div class="task-desc">${task.description}</div>` : ''}
        <div class="task-footer">
            <div class="task-badges">
                ${badgesHTML}
            </div>
        </div>
        <div class="task-actions">
            <button class="btn-action edit-btn" title="Editar">✏️ Editar</button>
            <button class="btn-action delete-btn" title="Eliminar">🗑️</button>
        </div>
    `;

    // Event Listeners for actions
    el.querySelector('.edit-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        openModal(task);
    });

    el.querySelector('.delete-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        if(confirm('¿Estás seguro de eliminar esta tarea permanentemente?')) {
            deleteTask(task.id);
        }
    });

    // Drag events attached to element
    el.addEventListener('dragstart', handleDragStart);
    el.addEventListener('dragend', handleDragEnd);

    return el;
}

// Modal Logic
function openModal(task = null) {
    const titleEl = document.getElementById('modal-title');
    taskForm.reset();
    
    if (task) {
        titleEl.textContent = 'Editar Tarea';
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-desc').value = task.description || '';
        document.getElementById('task-bucket').value = task.bucket;
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-user').value = task.user;
        document.getElementById('task-month').value = task.month_filter;
        document.getElementById('task-due-date').value = task.due_date || '';
    } else {
        titleEl.textContent = 'Agregar Nueva Tarea';
        document.getElementById('task-id').value = '';
    }
    
    taskModal.classList.add('active');
}

function closeModal() {
    taskModal.classList.remove('active');
}

async function handleTaskSubmit(e) {
    e.preventDefault();
    
    const id = document.getElementById('task-id').value;
    const taskData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-desc').value,
        bucket: document.getElementById('task-bucket').value,
        priority: document.getElementById('task-priority').value,
        user: document.getElementById('task-user').value,
        month_filter: document.getElementById('task-month').value,
        due_date: document.getElementById('task-due-date').value || null
    };
    
    try {
        let response;
        if (id) {
            // Update
            response = await fetch(`${API_BASE}${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            });
        } else {
            // Create
            response = await fetch(API_BASE, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            });
        }
        
        if (response.ok) {
            closeModal();
        }
    } catch (error) {
        console.error('Error saving task:', error);
    }
}

async function deleteTask(id) {
    try {
        await fetch(`${API_BASE}${id}`, { method: 'DELETE' });
    } catch (error) {
        console.error('Error deleting task:', error);
    }
}

async function updateTaskBucket(id, newBucket) {
    const task = tasks.find(t => t.id == id);
    if (!task || task.bucket === newBucket) return;
    
    try {
        await fetch(`${API_BASE}${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bucket: newBucket })
        });
    } catch (error) {
        console.error('Error updating task bucket:', error);
    }
}

// Drag and Drop Logic
let draggedCard = null;

function handleDragStart(e) {
    draggedCard = this;
    setTimeout(() => this.classList.add('dragging'), 0);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.dataset.id);
}

function handleDragEnd() {
    this.classList.remove('dragging');
    draggedCard = null;
    document.querySelectorAll('.bcol').forEach(col => col.classList.remove('drag-over'));
}

function setupDragAndDrop() {
    const columns = document.querySelectorAll('.bcol');
    
    columns.forEach(col => {
        col.addEventListener('dragover', e => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            col.classList.add('drag-over');
        });
        
        col.addEventListener('dragleave', () => {
            col.classList.remove('drag-over');
        });
        
        col.addEventListener('drop', e => {
            e.preventDefault();
            col.classList.remove('drag-over');
            
            const taskId = e.dataTransfer.getData('text/plain');
            const newBucket = col.dataset.bucket;
            
            if (taskId && newBucket) {
                updateTaskBucket(taskId, newBucket);
            }
        });
    });
}

// WebSocket Logic
function setupWebSockets() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        connectionStatus.textContent = 'En Vivo';
        connectionStatus.className = 'status-badge online';
    };
    
    ws.onclose = () => {
        connectionStatus.textContent = 'Desconectado';
        connectionStatus.className = 'status-badge offline';
        // Try to reconnect after 3 seconds
        setTimeout(setupWebSockets, 3000);
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
            case 'TASK_ADDED':
                tasks.push(message.task);
                renderTasks();
                break;
            case 'TASK_UPDATED':
                const index = tasks.findIndex(t => t.id === message.task.id);
                if (index !== -1) {
                    tasks[index] = { ...tasks[index], ...message.task };
                    renderTasks();
                }
                break;
            case 'TASK_DELETED':
                tasks = tasks.filter(t => t.id !== message.task_id);
                renderTasks();
                break;
        }
    };
}
