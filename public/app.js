/**
 * AnimauxTikTok Studio — Interactive Web App Logic
 * Features:
 * - TikTok Vertical 9:16 Video Player with smooth transitions
 * - Real Video Gallery with direct HTML5 video playback
 * - Dynamic Synchronized Subtitles with Karaoke highlighting
 * - Native French Spoken Voice Narration (Web Speech API + MP3 Audio)
 * - Canvas Audio Waveform Visualizer
 * - 104 Animals Database Explorer & Search
 * - On-Demand & Batch MP4 Video Generation (< 1 min, NO Arena logo)
 */

let ANIMALS = [];
let currentIndex = 0;
let isPlaying = false;
let isMuted = false;
let playbackSpeed = 1.0;
let isSpeaking = false;
let currentSpeechUtterance = null;
let visualizerAnimationId = null;

// DOM Elements
const mainVideo = document.getElementById('mainVideo');
const fallbackImg = document.getElementById('fallbackImg');
const visualizerCanvas = document.getElementById('visualizerCanvas');
const subtitleText = document.getElementById('subtitleText');
const speechIndicator = document.getElementById('speechIndicator');

const feedEmoji = document.getElementById('feedEmoji');
const feedTitle = document.getElementById('feedTitle');
const feedLatin = document.getElementById('feedLatin');
const feedSuperpower = document.getElementById('feedSuperpower');

const bioTitle = document.getElementById('bioTitle');
const bioCategory = document.getElementById('bioCategory');
const bioHabitat = document.getElementById('bioHabitat');
const bioSpeed = document.getElementById('bioSpeed');
const bioLifespan = document.getElementById('bioLifespan');
const bioDuration = document.getElementById('bioDuration');
const bioStoryText = document.getElementById('bioStoryText');

const sidebarList = document.getElementById('sidebarList');
const sidebarCount = document.getElementById('sidebarCount');
const galleryGrid = document.getElementById('galleryGrid');
const galleryCount = document.getElementById('galleryCount');
const readyCountBadge = document.getElementById('readyCountBadge');
const animalsGrid = document.getElementById('animalsGrid');
const resultsCount = document.getElementById('resultsCount');

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  setupTabs();
  setupSearch();
  setupCategories();
  setupControls();
  setupCanvas();
  await loadAnimals();
});

// Setup Canvas for Audio Visualizer
function setupCanvas() {
  const ctx = visualizerCanvas.getContext('2d');
  visualizerCanvas.width = 380;
  visualizerCanvas.height = 120;

  function renderVisualizer() {
    ctx.clearRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);
    if (!mainVideo.paused || isSpeaking) {
      const numBars = 24;
      const barWidth = 8;
      const spacing = 6;
      const startX = (visualizerCanvas.width - (numBars * (barWidth + spacing))) / 2;
      const time = Date.now() * 0.006 * playbackSpeed;

      for (let i = 0; i < numBars; i++) {
        const height = 12 + Math.abs(Math.sin(time + i * 0.4) * Math.cos(time * 0.7 + i * 0.2)) * 55;
        const x = startX + i * (barWidth + spacing);
        const y = visualizerCanvas.height - height - 10;

        const grad = ctx.createLinearGradient(0, y, 0, visualizerCanvas.height);
        grad.addColorStop(0, '#F59E0B');
        grad.addColorStop(1, 'rgba(245, 158, 11, 0.2)');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, height, 4);
        ctx.fill();
      }
    }
    visualizerAnimationId = requestAnimationFrame(renderVisualizer);
  }
  renderVisualizer();
}

// Fetch Animals Dataset
async function loadAnimals() {
  try {
    const res = await fetch('/api/animals');
    ANIMALS = await res.json();
    sidebarCount.textContent = ANIMALS.length;
    
    const readyVideos = ANIMALS.filter(a => a.video_status === 'ready');
    galleryCount.textContent = readyVideos.length;
    readyCountBadge.textContent = readyVideos.length;

    renderSidebar(ANIMALS);
    renderGallery(ANIMALS);
    renderGrid(ANIMALS);
    renderTable(ANIMALS);
    loadAnimal(0);
    updateStatsOverview();
  } catch (err) {
    console.error('Error loading animals:', err);
  }
}

// Load Specific Animal in Feed View
function loadAnimal(index) {
  if (index < 0 || index >= ANIMALS.length) return;
  currentIndex = index;
  const animal = ANIMALS[currentIndex];

  // Update Top Info Badge
  feedEmoji.textContent = animal.emoji || '🐾';
  feedTitle.textContent = (animal.name || '').toUpperCase();
  feedLatin.textContent = `${animal.latin || ''} • ${animal.title || ''}`;
  feedSuperpower.textContent = `✨ ${animal.superpower || 'Animal extraordinaire'}`;

  // Update Right Bio Drawer
  bioTitle.textContent = `${animal.emoji || ''} ${animal.name || ''}`;
  bioCategory.textContent = animal.category || '';
  bioHabitat.textContent = animal.habitat || 'Savanes et forêts';
  bioSpeed.textContent = animal.speed || 'Variable';
  bioLifespan.textContent = animal.lifespan || '15 ans';
  bioDuration.textContent = `< ${Math.ceil(animal.captions ? animal.captions[animal.captions.length - 1].end + 1 : 28)}s`;
  bioStoryText.textContent = animal.story || '';

  // Update Download Links
  const mp4Link = document.getElementById('mp4DownloadLink');
  const srtLink = document.getElementById('downloadSrtBtn').querySelector('a');
  mp4Link.href = animal.video_url || `/videos/${animal.id}.mp4`;
  srtLink.href = `/api/srt/${animal.id}.srt`;

  // Update Sidebar active item
  document.querySelectorAll('.sidebar-item').forEach((el, idx) => {
    el.classList.toggle('active', idx === currentIndex);
  });

  // Media Source Setup: ALWAYS load the video first
  const videoSrc = animal.video_url || `/videos/${animal.id}.mp4`;
  mainVideo.src = videoSrc;
  mainVideo.poster = animal.image_url || `/images/${animal.id}.png`;
  mainVideo.style.display = 'block';
  fallbackImg.style.display = 'none';

  mainVideo.load();
  mainVideo.play().catch(() => {
    // Autoplay might require user interaction
  });

  // Reset Subtitle
  subtitleText.textContent = animal.captions && animal.captions[0] ? animal.captions[0].text : animal.story.slice(0, 75) + '...';

  // Update Render button status
  const renderIcon = document.getElementById('renderIcon');
  const renderLabel = document.getElementById('renderLabel');
  if (animal.video_status === 'ready') {
    renderIcon.textContent = '✅';
    renderLabel.textContent = 'Prêt';
  } else {
    renderIcon.textContent = '🎬';
    renderLabel.textContent = 'Générer';
  }

  // Stop any active speech
  stopSpeech();
}

// Subtitle Synchronization
mainVideo.addEventListener('timeupdate', () => {
  const animal = ANIMALS[currentIndex];
  if (!animal) return;

  const curTime = mainVideo.currentTime;

  // Find active caption
  if (animal.captions) {
    const activeCap = animal.captions.find(c => curTime >= c.start && curTime <= c.end + 0.3);
    if (activeCap) {
      subtitleText.innerHTML = highlightWords(activeCap.text, curTime - activeCap.start, activeCap.end - activeCap.start);
    }
  }
});

// Word Highlight (Karaoke Effect)
function highlightWords(text, elapsed, capDuration) {
  const words = text.split(' ');
  const progressRatio = Math.min(Math.max(elapsed / Math.max(capDuration, 0.1), 0), 1);
  const activeWordIndex = Math.floor(progressRatio * words.length);

  return words.map((w, i) => {
    if (i === activeWordIndex) {
      return `<span class="subtitle-highlight">${w}</span>`;
    }
    return w;
  }).join(' ');
}

// Native French Spoken Voice Synthesizer
function speakStory(animal) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(animal.story);
  utterance.lang = 'fr-FR';
  utterance.rate = 1.02 * playbackSpeed;
  utterance.pitch = 1.0;

  const voices = window.speechSynthesis.getVoices();
  const frVoice = voices.find(v => v.lang.startsWith('fr'));
  if (frVoice) utterance.voice = frVoice;

  utterance.onstart = () => {
    isSpeaking = true;
    speechIndicator.style.display = 'flex';
  };

  utterance.onend = () => {
    isSpeaking = false;
    speechIndicator.style.display = 'none';
  };

  utterance.onerror = () => {
    isSpeaking = false;
    speechIndicator.style.display = 'none';
  };

  window.speechSynthesis.speak(utterance);
  currentSpeechUtterance = utterance;
}

function stopSpeech() {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  isSpeaking = false;
  speechIndicator.style.display = 'none';
}

// Setup Player Controls & Action Bar
function setupControls() {
  // Up / Down Buttons
  document.getElementById('nextVideoBtn').addEventListener('click', () => {
    if (currentIndex < ANIMALS.length - 1) loadAnimal(currentIndex + 1);
  });
  document.getElementById('prevVideoBtn').addEventListener('click', () => {
    if (currentIndex > 0) loadAnimal(currentIndex - 1);
  });

  // Keyboard Navigation
  window.addEventListener('keydown', (e) => {
    if (document.activeElement.tagName === 'INPUT') return;
    if (e.key === 'ArrowDown' || e.key === 'j') {
      if (currentIndex < ANIMALS.length - 1) loadAnimal(currentIndex + 1);
    } else if (e.key === 'ArrowUp' || e.key === 'k') {
      if (currentIndex > 0) loadAnimal(currentIndex - 1);
    }
  });

  // Speed Selector
  const speedBtn = document.getElementById('speedToggleBtn');
  speedBtn.addEventListener('click', () => {
    if (playbackSpeed === 1.0) playbackSpeed = 1.25;
    else if (playbackSpeed === 1.25) playbackSpeed = 1.5;
    else playbackSpeed = 1.0;

    mainVideo.playbackRate = playbackSpeed;
    document.getElementById('speedIcon').textContent = `${playbackSpeed}x`;
  });

  // French Voice Button
  const ttsBtn = document.getElementById('ttsSpeakBtn');
  ttsBtn.addEventListener('click', () => {
    const animal = ANIMALS[currentIndex];
    if (isSpeaking) stopSpeech();
    else speakStory(animal);
  });

  // Like Button Animation
  const likeBtn = document.getElementById('likeBtn');
  likeBtn.addEventListener('click', () => {
    const circle = likeBtn.querySelector('.action-circle');
    circle.classList.toggle('active');
    const count = document.getElementById('likeCount');
    count.textContent = '2.5k';
  });

  // Render on-demand button
  const renderBtn = document.getElementById('renderMp4Btn');
  renderBtn.addEventListener('click', async () => {
    const animal = ANIMALS[currentIndex];
    document.getElementById('renderIcon').textContent = '⏳';
    document.getElementById('renderLabel').textContent = 'Rendu...';

    try {
      await fetch(`/api/generate/${animal.id}`, { method: 'POST' });
      setTimeout(async () => {
        await loadAnimals();
      }, 3000);
    } catch (e) {
      console.error(e);
    }
  });

  // Bio Drawer actions
  document.getElementById('drawerPlayAudioBtn').addEventListener('click', () => {
    const animal = ANIMALS[currentIndex];
    speakStory(animal);
  });

  document.getElementById('drawerDownloadMp4Btn').addEventListener('click', () => {
    const animal = ANIMALS[currentIndex];
    const link = document.createElement('a');
    link.href = animal.video_url || `/videos/${animal.id}.mp4`;
    link.download = `${animal.id}_story.mp4`;
    link.click();
  });

  // Batch Generation Buttons
  const batchBtn = document.getElementById('generateBatchBtn');
  if (batchBtn) {
    batchBtn.addEventListener('click', async () => {
      batchBtn.disabled = true;
      batchBtn.innerHTML = '<span>⏳</span> Rendu en cours...';
      try {
        await fetch('/api/generate-all', { method: 'POST' });
        document.getElementById('queueStatusBadge').textContent = 'En cours de rendu';
        pollBatchStatus();
      } catch (e) {
        console.error(e);
      }
    });
  }
}

// Poll Batch Status
async function pollBatchStatus() {
  const interval = setInterval(async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      const pct = Math.round((data.ready / data.total) * 100);
      document.getElementById('batchProgressFill').style.width = `${pct}%`;
      document.getElementById('queueDetailText').textContent = `${data.ready} vidéos générées sur ${data.total} prêtes pour le téléchargement immédiat.`;
      document.getElementById('statReadyVideos').textContent = data.ready;
      galleryCount.textContent = data.ready;
      readyCountBadge.textContent = data.ready;

      if (data.queue === 0) {
        clearInterval(interval);
        document.getElementById('queueStatusBadge').textContent = 'Terminé ✅';
        loadAnimals();
      }
    } catch (e) {
      clearInterval(interval);
    }
  }, 2500);
}

// Navigation Tabs Setup
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const tabId = btn.getAttribute('data-tab');
      document.getElementById(`${tabId}Section`).classList.add('active');
    });
  });
}

// Category Filter Setup
function setupCategories() {
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const cat = chip.getAttribute('data-category');
      filterAnimals(cat, document.getElementById('searchInput').value);
    });
  });
}

// Search Setup
function setupSearch() {
  const input = document.getElementById('searchInput');
  const clearBtn = document.getElementById('clearSearch');

  input.addEventListener('input', () => {
    const val = input.value.trim();
    clearBtn.style.display = val ? 'block' : 'none';
    const activeChip = document.querySelector('.chip.active');
    const cat = activeChip ? activeChip.getAttribute('data-category') : 'all';
    filterAnimals(cat, val);
  });

  clearBtn.addEventListener('click', () => {
    input.value = '';
    clearBtn.style.display = 'none';
    const activeChip = document.querySelector('.chip.active');
    const cat = activeChip ? activeChip.getAttribute('data-category') : 'all';
    filterAnimals(cat, '');
  });
}

// Filter Function
function filterAnimals(category, query) {
  let filtered = ANIMALS;

  if (category && category !== 'all') {
    filtered = filtered.filter(a => a.category === category);
  }

  if (query) {
    const q = query.toLowerCase();
    filtered = filtered.filter(a =>
      a.name.toLowerCase().includes(q) ||
      a.latin.toLowerCase().includes(q) ||
      a.habitat.toLowerCase().includes(q) ||
      a.story.toLowerCase().includes(q)
    );
  }

  resultsCount.textContent = `${filtered.length} animaux affichés`;
  sidebarCount.textContent = filtered.length;
  renderSidebar(filtered);
  renderGallery(filtered);
  renderGrid(filtered);
  renderTable(filtered);
}

// Render Left Sidebar List
function renderSidebar(list) {
  sidebarList.innerHTML = list.map((a, idx) => `
    <div class="sidebar-item ${idx === currentIndex ? 'active' : ''}" onclick="selectAnimalById('${a.id}')">
      <span class="sidebar-emoji">${a.emoji || '🐾'}</span>
      <span class="sidebar-title">${a.name}</span>
      <span class="sidebar-ready">${a.video_status === 'ready' ? '🎬' : '⚡'}</span>
    </div>
  `).join('');
}

// Render Videos Gallery Tab (Direct HTML5 Videos)
function renderGallery(list) {
  const readyList = list.filter(a => a.video_status === 'ready' || a.video_url);
  galleryGrid.innerHTML = readyList.map(a => `
    <div class="video-card-player">
      <div class="video-card-media">
        <video src="${a.video_url || '/videos/' + a.id + '.mp4'}" controls playsinline preload="metadata" poster="${a.image_url || '/images/' + a.id + '.png'}"></video>
      </div>
      <div class="video-card-info">
        <div class="video-card-header">
          <span style="font-size:24px;">${a.emoji || '🐾'}</span>
          <div>
            <h4 class="video-card-title">${a.name}</h4>
            <span class="video-card-sub">${a.category} • « ${a.title} »</span>
          </div>
        </div>
        <p class="video-card-story">${a.story}</p>
        <div class="video-card-actions">
          <button class="btn btn-primary" onclick="openFeedWithAnimal('${a.id}')">
            <span>📱</span> Plein Écran Feed
          </button>
          <a class="btn btn-secondary" href="${a.video_url || '/videos/' + a.id + '.mp4'}" download>
            <span>📥</span> MP4
          </a>
          <a class="btn btn-outline" href="/api/srt/${a.id}.srt" download>
            <span>📝</span> SRT
          </a>
        </div>
      </div>
    </div>
  `).join('');
}

// Render Encyclopedia Grid
function renderGrid(list) {
  animalsGrid.innerHTML = list.map(a => `
    <div class="animal-card">
      <div class="card-img-wrapper" onclick="openFeedWithAnimal('${a.id}')">
        <img src="${a.image_url || '/images/' + a.id + '.png'}" class="card-img" alt="${a.name}" loading="lazy" />
        <span class="card-category-tag">${a.category}</span>
        <span class="card-dur-tag">&lt; 30s</span>
      </div>
      <div class="card-body">
        <div class="card-title-row">
          <span class="card-emoji">${a.emoji || '🐾'}</span>
          <h3 class="card-name">${a.name}</h3>
        </div>
        <p class="card-latin">${a.latin} • « ${a.title} »</p>
        <p class="card-story-preview">${a.story}</p>
        <div class="card-footer-actions">
          <button class="btn btn-primary" onclick="openFeedWithAnimal('${a.id}')">
            <span>🎬</span> Regarder
          </button>
          <a class="btn btn-secondary" href="${a.video_url || '/videos/' + a.id + '.mp4'}" download>
            <span>📥</span> MP4
          </a>
        </div>
      </div>
    </div>
  `).join('');
}

// Render Videos Table in Studio View
function renderTable(list) {
  const tbody = document.getElementById('videosTableBody');
  tbody.innerHTML = list.map(a => `
    <tr>
      <td><strong>${a.emoji || ''} ${a.name}</strong><br><small style="color:var(--text-muted)">${a.latin}</small></td>
      <td>${a.category}</td>
      <td>Vertical 9:16 (720x1280)</td>
      <td>&lt; 30s</td>
      <td>
        <span class="status-tag ${a.video_status === 'ready' ? 'status-ready' : 'status-pending'}">
          ${a.video_status === 'ready' ? '✅ MP4 Prêt' : '⚡ À générer'}
        </span>
      </td>
      <td>
        <div style="display:flex; gap:6px;">
          <button class="btn btn-secondary" style="padding:6px 10px; font-size:11px;" onclick="openFeedWithAnimal('${a.id}')">
            🎬 Voir
          </button>
          <a class="btn btn-primary" style="padding:6px 10px; font-size:11px;" href="${a.video_url || '/videos/' + a.id + '.mp4'}" download>
            📥 MP4
          </a>
          <a class="btn btn-outline" style="padding:6px 10px; font-size:11px;" href="/api/srt/${a.id}.srt" download>
            📝 SRT
          </a>
        </div>
      </td>
    </tr>
  `).join('');
}

// Helper: Open Feed Directly on selected Animal
window.openFeedWithAnimal = function(id) {
  const index = ANIMALS.findIndex(a => a.id === id);
  if (index !== -1) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    document.querySelector('.tab-btn[data-tab="feed"]').classList.add('active');
    document.getElementById('feedSection').classList.add('active');
    loadAnimal(index);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
};

window.selectAnimalById = function(id) {
  const index = ANIMALS.findIndex(a => a.id === id);
  if (index !== -1) {
    loadAnimal(index);
  }
};

// Update Stats in Generator View
function updateStatsOverview() {
  const readyCount = ANIMALS.filter(a => a.video_status === 'ready').length;
  document.getElementById('statTotalAnimals').textContent = ANIMALS.length;
  document.getElementById('statReadyVideos').textContent = readyCount;
  const pct = Math.round((readyCount / ANIMALS.length) * 100);
  document.getElementById('batchProgressFill').style.width = `${pct}%`;
}
