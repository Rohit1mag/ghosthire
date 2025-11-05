// Global state
let allJobs = [];
let filteredJobs = [];
let selectedTech = new Set();
let currentSort = 'score';
let currentView = 'grid';
let savedJobs = new Set(JSON.parse(localStorage.getItem('savedJobs') || '[]'));

// DOM elements
const jobsContainer = document.getElementById('jobs-container');
const searchInput = document.getElementById('search');
const locationSelect = document.getElementById('location');
const techFilter = document.getElementById('tech-filter');
const clearFiltersBtn = document.getElementById('clear-filters');
const jobCount = document.getElementById('job-count');
const lastUpdated = document.getElementById('last-updated');
const loadingState = document.querySelector('.loading-state');
const emptyState = document.querySelector('.empty-state');

// Load jobs from JSON
async function loadJobs() {
    try {
        if (loadingState) loadingState.style.display = 'block';
        if (emptyState) emptyState.style.display = 'none';
        
        const response = await fetch('jobs.json');
        if (!response.ok) {
            throw new Error('Failed to load jobs.json');
        }
        const data = await response.json();
        allJobs = data;
        
        // Update last updated time
        if (lastUpdated) {
            const updateTime = new Date().toLocaleString();
            lastUpdated.textContent = updateTime;
        }
        
        // Initialize filters
        initializeFilters();
        
        // Apply filters
        applyFilters();
        
        if (loadingState) loadingState.style.display = 'none';
    } catch (error) {
        console.error('Error loading jobs:', error);
        if (loadingState) loadingState.style.display = 'none';
        if (emptyState) {
            emptyState.style.display = 'block';
            emptyState.querySelector('.empty-state-title').textContent = 'Failed to load jobs';
            emptyState.querySelector('.empty-state-description').textContent = 'Make sure jobs.json exists.';
        } else {
            jobsContainer.innerHTML = '<div class="no-jobs">Failed to load jobs. Make sure jobs.json exists.</div>';
        }
    }
}

// Initialize filter dropdowns and tech tags
function initializeFilters() {
    // Get unique locations
    const locations = [...new Set(allJobs.map(job => job.location).filter(Boolean))].sort();
    locationSelect.innerHTML = '<option value="">All Locations</option>';
    locations.forEach(loc => {
        const option = document.createElement('option');
        option.value = loc;
        option.textContent = loc;
        locationSelect.appendChild(option);
    });
    
    // Get all tech stack items
    const allTech = new Set();
    allJobs.forEach(job => {
        job.tech_stack.forEach(tech => allTech.add(tech));
    });
    
    // Create tech filter tags
    techFilter.innerHTML = '';
    [...allTech].sort().forEach(tech => {
        const tag = document.createElement('span');
        tag.className = 'tech-tag';
        tag.textContent = tech;
        tag.dataset.tech = tech;
        tag.addEventListener('click', () => toggleTechFilter(tech));
        techFilter.appendChild(tag);
    });
}

// Toggle tech filter
function toggleTechFilter(tech) {
    const tag = document.querySelector(`[data-tech="${tech}"]`);
    if (selectedTech.has(tech)) {
        selectedTech.delete(tech);
        tag.classList.remove('active');
    } else {
        selectedTech.add(tech);
        tag.classList.add('active');
    }
    applyFilters();
}

// Apply all filters
function applyFilters() {
    let filtered = [...allJobs];
    
    // Search filter
    const searchTerm = searchInput.value.toLowerCase().trim();
    if (searchTerm) {
        filtered = filtered.filter(job => 
            job.company.toLowerCase().includes(searchTerm) ||
            job.title.toLowerCase().includes(searchTerm)
        );
    }
    
    // Location filter
    const locationValue = locationSelect.value;
    if (locationValue) {
        filtered = filtered.filter(job => job.location === locationValue);
    }
    
    // Tech stack filter
    if (selectedTech.size > 0) {
        filtered = filtered.filter(job => 
            job.tech_stack.some(tech => selectedTech.has(tech))
        );
    }
    
    filteredJobs = filtered;
    renderJobs();
    updateStats();
}

// Calculate time ago
function getTimeAgo(dateString) {
    if (!dateString) return 'Recently';
    
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 3600) return 'Just now';
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    const days = Math.floor(seconds / 86400);
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days}d ago`;
    if (days < 30) return `${Math.floor(days / 7)}w ago`;
    return `${Math.floor(days / 30)}mo ago`;
}

// Get freshness badge
function getFreshnessBadge(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const days = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (days <= 1) return '<span class="freshness-badge fresh">🔥 New</span>';
    if (days <= 7) return '<span class="freshness-badge recent">Recent</span>';
    return '';
}

// Toggle save job
function toggleSaveJob(jobId, event) {
    event.preventDefault();
    event.stopPropagation();
    
    if (savedJobs.has(jobId)) {
        savedJobs.delete(jobId);
    } else {
        savedJobs.add(jobId);
    }
    
    localStorage.setItem('savedJobs', JSON.stringify([...savedJobs]));
    
    // Update button
    const button = event.currentTarget;
    const icon = button.querySelector('i');
    if (savedJobs.has(jobId)) {
        icon.classList.remove('far');
        icon.classList.add('fas');
        button.classList.add('saved');
    } else {
        icon.classList.remove('fas');
        icon.classList.add('far');
        button.classList.remove('saved');
    }
}

// Render jobs
function renderJobs() {
    if (filteredJobs.length === 0) {
        if (emptyState) {
            emptyState.style.display = 'block';
        } else {
            jobsContainer.innerHTML = '<div class="no-jobs">No jobs found matching your filters.</div>';
        }
        return;
    }
    
    if (emptyState) emptyState.style.display = 'none';
    
    // Sort jobs
    let sortedJobs = [...filteredJobs];
    if (currentSort === 'score') {
        sortedJobs.sort((a, b) => (b.hidden_score || 0) - (a.hidden_score || 0));
    } else if (currentSort === 'date') {
        sortedJobs.sort((a, b) => {
            const dateA = new Date(a.posted_date || a.scraped_at || 0);
            const dateB = new Date(b.posted_date || b.scraped_at || 0);
            return dateB - dateA;
        });
    }
    
    jobsContainer.innerHTML = sortedJobs.map(job => {
        const isSaved = savedJobs.has(job.id);
        const timeAgo = getTimeAgo(job.posted_date || job.scraped_at);
        const freshnessBadge = getFreshnessBadge(job.posted_date || job.scraped_at);
        
        return `
        <div class="job-card" data-job-id="${job.id}">
            <div class="job-card-header">
                <div class="job-header-left">
                    <div class="job-company">${escapeHtml(job.company)}</div>
                    <div class="job-title">${escapeHtml(job.title)}</div>
                </div>
                <button class="save-button ${isSaved ? 'saved' : ''}" onclick="toggleSaveJob('${job.id}', event)" title="${isSaved ? 'Unsave' : 'Save'} job">
                    <i class="${isSaved ? 'fas' : 'far'} fa-bookmark"></i>
                </button>
            </div>
            
            <div class="job-meta-row">
                ${job.location ? `<span class="job-meta-item"><i class="fas fa-map-marker-alt"></i> ${escapeHtml(job.location)}</span>` : ''}
                <span class="job-meta-item"><i class="far fa-clock"></i> ${timeAgo}</span>
                <span class="job-source-badge">${escapeHtml(job.source)}</span>
            </div>
            
            ${job.tech_stack && job.tech_stack.length > 0 ? `
                <div class="job-tech-stack">
                    ${job.tech_stack.slice(0, 5).map(tech => `<span class="tech-badge">${escapeHtml(tech)}</span>`).join('')}
                    ${job.tech_stack.length > 5 ? `<span class="tech-badge-more">+${job.tech_stack.length - 5} more</span>` : ''}
                </div>
            ` : ''}
            
            <div class="job-card-footer">
                <div class="job-score-info">
                    ${freshnessBadge}
                    <span class="hidden-score-badge">
                        <i class="fas fa-star"></i>
                        <span class="score-value">${job.hidden_score || 0}</span>
                        <span class="score-label">Hidden Score</span>
                    </span>
                </div>
                <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer" class="apply-button">
                    <span>Apply Now</span>
                    <i class="fas fa-arrow-right"></i>
                </a>
            </div>
        </div>
        `;
    }).join('');
    
    // Update view class
    if (currentView === 'list') {
        jobsContainer.classList.add('list-view');
    } else {
        jobsContainer.classList.remove('list-view');
    }
}

// Update stats
function updateStats() {
    const savedCount = savedJobs.size;
    jobCount.textContent = `${filteredJobs.length} job${filteredJobs.length !== 1 ? 's' : ''} found`;
    
    // Update saved jobs count if badge exists
    const savedBadge = document.querySelector('.saved-jobs-badge');
    if (savedBadge) {
        savedBadge.textContent = savedCount;
        savedBadge.style.display = savedCount > 0 ? 'inline-block' : 'none';
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Clear all filters
function clearFilters() {
    searchInput.value = '';
    locationSelect.value = '';
    selectedTech.clear();
    document.querySelectorAll('.tech-tag').forEach(tag => tag.classList.remove('active'));
    applyFilters();
}

// Sort handler
function handleSort(sortType) {
    currentSort = sortType;
    document.querySelectorAll('.sort-option').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-sort="${sortType}"]`).classList.add('active');
    renderJobs();
}

// View handler
function handleView(viewType) {
    currentView = viewType;
    document.querySelectorAll('.view-option').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-view="${viewType}"]`).classList.add('active');
    renderJobs();
}

// Event listeners
if (searchInput) {
    searchInput.addEventListener('input', applyFilters);
}
if (locationSelect) {
    locationSelect.addEventListener('change', applyFilters);
}
if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', clearFilters);
}

// Sort options
document.querySelectorAll('.sort-option').forEach(btn => {
    btn.addEventListener('click', () => handleSort(btn.dataset.sort));
});

// View options
document.querySelectorAll('.view-option').forEach(btn => {
    btn.addEventListener('click', () => handleView(btn.dataset.view));
});

// Newsletter form
const newsletterForm = document.querySelector('.newsletter-form');
if (newsletterForm) {
    newsletterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        alert('Newsletter subscription coming soon!');
    });
}

// Reset filters button
const resetFiltersBtn = document.getElementById('reset-filters');
if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener('click', clearFilters);
}

// Refresh data button
const refreshDataBtn = document.getElementById('refresh-data');
if (refreshDataBtn) {
    refreshDataBtn.addEventListener('click', () => {
        loadJobs();
    });
}

// Load jobs on page load
loadJobs();

