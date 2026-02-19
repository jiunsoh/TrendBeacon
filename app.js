// Initialize Charts
document.addEventListener('DOMContentLoaded', () => {
    initPerformanceChart();
    populateTrends();
    setupEventListeners();
});

function initPerformanceChart() {
    const ctx = document.getElementById('performanceChart').getContext('2d');

    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(254, 44, 85, 0.3)');
    gradient.addColorStop(1, 'rgba(254, 44, 85, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Views',
                data: [12000, 19000, 15000, 25000, 22000, 30000, 45000],
                borderColor: '#FE2C55',
                borderWidth: 3,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#FE2C55',
                pointBorderColor: '#fff',
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#A9A9A9'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#A9A9A9'
                    }
                }
            }
        }
    });
}

function populateTrends() {
    const hashtags = [
        { name: '#fyp', views: '45.2B', growth: '+12%' },
        { name: '#tiktokmademebuyit', views: '12.8B', growth: '+24%' },
        { name: '#techhacks', views: '2.4B', growth: '+8%' },
        { name: '#wintervibes', views: '840M', growth: '+45%' },
        { name: '#asmr', views: '18.1B', growth: '-2%' }
    ];

    const sounds = [
        { name: 'Lo-fi Beats for Studying', artist: 'Studying Girl', usage: '1.2M posts' },
        { name: 'Happy Upbeat Theme', artist: 'StockAudio', usage: '840K posts' },
        { name: 'Dramatic Orchestral', artist: 'Epic Scores', usage: '420K posts' },
        { name: 'Nature Sounds', artist: 'Zen Vibes', usage: '210K posts' }
    ];

    const tagContainer = document.getElementById('hashtag-trends');
    const soundContainer = document.getElementById('sound-trends');

    tagContainer.innerHTML = hashtags.map((h, i) => `
        <div class="trend-item">
            <span class="trend-rank">${i + 1}</span>
            <div class="trend-info">
                <div class="trend-name">${h.name}</div>
                <div class="trend-meta">${h.views} views</div>
            </div>
            <span class="stat-trend ${h.growth.startsWith('+') ? 'trend-up' : 'trend-down'}">${h.growth}</span>
        </div>
    `).join('');

    soundContainer.innerHTML = sounds.map((s, i) => `
        <div class="trend-item">
            <div class="trend-info">
                <div class="trend-name">${s.name}</div>
                <div class="trend-meta">${s.artist} • ${s.usage}</div>
            </div>
            <i class="fas fa-play" style="font-size: 0.8rem; color: var(--text-secondary);"></i>
        </div>
    `).join('');
}

function setupEventListeners() {
    const connectBtn = document.getElementById('connectBtn');
    const modal = document.getElementById('connectModal');

    connectBtn.addEventListener('click', () => {
        modal.style.display = 'flex';
    });

    // Close modal on outside click
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };
}

function switchTab(tabId) {
    // UI logic for switching nav items
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.innerText.toLowerCase().includes(tabId)) {
            item.classList.add('active');
        }
    });

    // In a real app, this would change the visible content
    console.log(`Switching to ${tabId} view`);
}
