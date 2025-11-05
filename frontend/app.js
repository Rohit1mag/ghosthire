// Global state
let allJobs = [];
let filteredJobs = [];
let selectedTech = new Set();

// DOM elements
const jobsContainer = document.getElementById('jobs-container');
const searchInput = document.getElementById('search');
const locationSelect = document.getElementById('location');
const techFilter = document.getElementById('tech-filter');
const clearFiltersBtn = document.getElementById('clear-filters');
const jobCount = document.getElementById('job-count');
const lastUpdated = document.getElementById('last-updated');

// Load jobs from JSON
async function loadJobs() {
    try {
        const response = await fetch('jobs.json');
        if (!response.ok) {
            throw new Error('Failed to load jobs.json');
        }
        const data = await response.json();
        allJobs = data;
        
        // Update last updated time
        const updateTime = new Date().toLocaleString();
        lastUpdated.textContent = updateTime;
        
        // Initialize filters
        initializeFilters();
        
        // Apply filters
        applyFilters();
    } catch (error) {
        console.error('Error loading jobs:', error);
        jobsContainer.innerHTML = '<div class="no-jobs">Failed to load jobs. Make sure jobs.json exists.</div>';
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

// Render jobs
function renderJobs() {
    if (filteredJobs.length === 0) {
        jobsContainer.innerHTML = '<div class="no-jobs">No jobs found matching your filters.</div>';
        return;
    }
    
    jobsContainer.innerHTML = filteredJobs.map(job => `
        <div class="job-card">
            <div class="job-header">
                <div>
                    <div class="job-company">${escapeHtml(job.company)}</div>
                    <div class="job-title">${escapeHtml(job.title)}</div>
                </div>
                <div class="hidden-score">${job.hidden_score || 0}</div>
            </div>
            
            ${job.location ? `<div class="job-location">📍 ${escapeHtml(job.location)}</div>` : ''}
            
            <div class="job-source">${escapeHtml(job.source)}</div>
            
            ${job.tech_stack.length > 0 ? `
                <div class="job-tech-stack">
                    ${job.tech_stack.map(tech => `<span class="tech-badge">${escapeHtml(tech)}</span>`).join('')}
                </div>
            ` : ''}
            
            <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer" class="apply-button">
                Apply Now →
            </a>
        </div>
    `).join('');
}

// Update stats
function updateStats() {
    jobCount.textContent = `${filteredJobs.length} job${filteredJobs.length !== 1 ? 's' : ''} found`;
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

// Event listeners
searchInput.addEventListener('input', applyFilters);
locationSelect.addEventListener('change', applyFilters);
clearFiltersBtn.addEventListener('click', clearFilters);

// Load jobs on page load
loadJobs();

