/**
 * TechResolve Admin - Simple Complaint Management
 * Handles complaint filtering and basic UI interactions
 */

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin JS loaded');

    // Initialize complaint filters if on complaints page
    if (document.getElementById('statusFilter')) {
        initializeComplaintFilters();
    }

    // Initialize log filters if on logs page
    if (document.getElementById('actionFilter')) {
        initializeLogFilters();
    }
});

// Initialize complaint filters
function initializeComplaintFilters() {
    console.log('Initializing complaint filters');

    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const searchFilter = document.getElementById('searchFilter');
    const archivedFilter = document.getElementById('archivedFilter');

    if (!applyFiltersBtn) {
        console.error('Apply Filters button not found!');
        return;
    }

    // Add click event listener to the button
    applyFiltersBtn.addEventListener('click', function(e) {
        e.preventDefault();
        console.log('Apply Filters button clicked');
        applyComplaintFilters();
    });

    // Allow pressing Enter in search field
    if (searchFilter) {
        searchFilter.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyComplaintFilters();
            }
        });
    }

    // Set initial filter from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const statusParam = urlParams.get('status');
    if (statusParam && statusFilter) {
        statusFilter.value = statusParam;
    }

    // Apply initial filters
    applyComplaintFilters();
}

// Apply complaint filters
function applyComplaintFilters() {
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const searchFilter = document.getElementById('searchFilter');
    const archivedFilter = document.getElementById('archivedFilter');

    if (!statusFilter || !priorityFilter || !searchFilter || !archivedFilter) {
        console.error('Filter elements not found');
        return;
    }

    const statusValue = statusFilter.value;
    const priorityValue = priorityFilter.value;
    const searchValue = searchFilter.value.trim().toLowerCase();
    const hideArchived = archivedFilter.checked;

    console.log('Applying filters:', { statusValue, priorityValue, searchValue, hideArchived });

    // Get all complaint rows
    const desktopRows = document.querySelectorAll('#complaintRows tr[data-status]');
    const mobileRows = document.querySelectorAll('#mobilecomplaintRows > div[data-status]');

    let visibleCount = 0;

    // Filter desktop rows
    desktopRows.forEach(row => {
        const matchesStatus = statusValue === 'all' || row.dataset.status === statusValue;
        const matchesPriority = priorityValue === 'all' || row.dataset.priority === priorityValue;
        const matchesSearch = !searchValue || row.dataset.search.includes(searchValue);
        const isArchived = row.dataset.archived === 'yes';
        const matchesArchived = !hideArchived || !isArchived;

        const visible = matchesStatus && matchesPriority && matchesSearch && matchesArchived;
        row.style.display = visible ? '' : 'none';

        if (visible) visibleCount++;
    });

    // Filter mobile rows
    mobileRows.forEach(row => {
        const matchesStatus = statusValue === 'all' || row.dataset.status === statusValue;
        const matchesPriority = priorityValue === 'all' || row.dataset.priority === priorityValue;
        const matchesSearch = !searchValue || row.dataset.search.includes(searchValue);
        const isArchived = row.dataset.archived === 'yes';
        const matchesArchived = !hideArchived || !isArchived;

        const visible = matchesStatus && matchesPriority && matchesSearch && matchesArchived;
        row.style.display = visible ? '' : 'none';
    });

    // Show/hide no results message
    const noResultsRow = document.querySelector('#complaintRows tr:not([data-status])');
    const noResultsMobile = document.querySelector('#mobilecomplaintRows > div:not([data-status])');

    if (noResultsRow) {
        noResultsRow.style.display = visibleCount === 0 ? '' : 'none';
    }
    if (noResultsMobile) {
        noResultsMobile.style.display = visibleCount === 0 ? '' : 'none';
    }

    console.log(`Filtered to ${visibleCount} visible complaints`);
}

// Initialize log filters
function initializeLogFilters() {
    console.log('Initializing log filters');

    const applyLogFiltersBtn = document.getElementById('applyLogFiltersBtn');
    const actionFilter = document.getElementById('actionFilter');
    const adminFilter = document.getElementById('adminFilter');
    const dateFilter = document.getElementById('dateFilter');
    const searchFilter = document.getElementById('searchFilter');

    if (!applyLogFiltersBtn) {
        console.error('Apply Log Filters button not found!');
        return;
    }

    // Add click event listener
    applyLogFiltersBtn.addEventListener('click', function(e) {
        e.preventDefault();
        console.log('Apply Log Filters button clicked');
        applyLogFilters();
    });

    // Allow pressing Enter in search field
    if (searchFilter) {
        searchFilter.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyLogFilters();
            }
        });
    }

    // Apply initial filters
    applyLogFilters();
}

// Apply log filters
function applyLogFilters() {
    const actionFilter = document.getElementById('actionFilter');
    const adminFilter = document.getElementById('adminFilter');
    const dateFilter = document.getElementById('dateFilter');
    const searchFilter = document.getElementById('searchFilter');

    if (!actionFilter || !adminFilter || !dateFilter || !searchFilter) {
        console.error('Log filter elements not found');
        return;
    }

    const actionValue = actionFilter.value;
    const adminValue = adminFilter.value;
    const dateValue = dateFilter.value;
    const searchValue = searchFilter.value.trim().toLowerCase();

    console.log('Applying log filters:', { actionValue, adminValue, dateValue, searchValue });

    // Get date range
    let dateFrom = null;
    if (dateValue === 'today') {
        dateFrom = new Date();
        dateFrom.setHours(0, 0, 0, 0);
    } else if (dateValue === 'yesterday') {
        dateFrom = new Date();
        dateFrom.setDate(dateFrom.getDate() - 1);
        dateFrom.setHours(0, 0, 0, 0);
    } else if (dateValue === 'week') {
        dateFrom = new Date();
        dateFrom.setDate(dateFrom.getDate() - 7);
        dateFrom.setHours(0, 0, 0, 0);
    } else if (dateValue === 'month') {
        dateFrom = new Date();
        dateFrom.setDate(dateFrom.getDate() - 30);
        dateFrom.setHours(0, 0, 0, 0);
    }

    // Get all log rows
    const desktopRows = document.querySelectorAll('#logRows tr[data-action]');
    const mobileRows = document.querySelectorAll('#mobileLogRows > div[data-action]');

    let visibleCount = 0;

    // Filter desktop rows
    desktopRows.forEach(row => {
        const matchesAction = actionValue === 'all' || row.dataset.action === actionValue;
        const matchesAdmin = adminValue === 'all' || row.dataset.admin === adminValue;
        const matchesSearch = !searchValue || row.textContent.toLowerCase().includes(searchValue);

        let matchesDate = true;
        if (dateFrom) {
            const rowDate = new Date(row.dataset.timestamp);
            matchesDate = rowDate >= dateFrom;
        }

        const visible = matchesAction && matchesAdmin && matchesSearch && matchesDate;
        row.style.display = visible ? '' : 'none';

        if (visible) visibleCount++;
    });

    // Filter mobile rows
    mobileRows.forEach(row => {
        const matchesAction = actionValue === 'all' || row.dataset.action === actionValue;
        const matchesAdmin = adminValue === 'all' || row.dataset.admin === adminValue;
        const matchesSearch = !searchValue || row.textContent.toLowerCase().includes(searchValue);

        let matchesDate = true;
        if (dateFrom) {
            const rowDate = new Date(row.dataset.timestamp);
            matchesDate = rowDate >= dateFrom;
        }

        const visible = matchesAction && matchesAdmin && matchesSearch && matchesDate;
        row.style.display = visible ? '' : 'none';
    });

    // Show/hide no results message
    const noResultsRow = document.querySelector('#logRows tr:not([data-action])');
    const noResultsMobile = document.querySelector('#mobileLogRows > div:not([data-action])');

    if (noResultsRow) {
        noResultsRow.style.display = visibleCount === 0 ? '' : 'none';
    }
    if (noResultsMobile) {
        noResultsMobile.style.display = visibleCount === 0 ? '' : 'none';
    }

    console.log(`Filtered to ${visibleCount} visible logs`);
}

// Utility functions
function showLoader() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.classList.remove('hidden');
    }
}

function hideLoader() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.classList.add('hidden');
    }
}

function showSuccessMessage(message) {
    createNotification(message, 'success');
}

function showErrorMessage(message) {
    createNotification(message, 'error');
}

function createNotification(message, type = 'success') {
    const container = document.getElementById('notification-container');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `alert mb-4 p-4 rounded-lg flex items-center justify-between ${type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`;

    notification.innerHTML = `
        <div class="flex items-center gap-2">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="text-gray-500 hover:text-gray-700" onclick="this.parentElement.remove()" aria-label="Dismiss notification">
            <i class="fas fa-times"></i>
            <span class="sr-only">Dismiss notification</span>
        </button>
    `;

    container.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 500);
    }, 5000);
}
