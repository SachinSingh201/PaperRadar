// Paper Radar — Client-side Search, Filtering, and Bookmarks
document.addEventListener('DOMContentLoaded', () => {
  // Theme Toggle
  const themeToggle = document.getElementById('theme-toggle');
  const html = document.documentElement;
  const savedTheme = localStorage.getItem('radar_theme') || 'dark';
  html.setAttribute('data-theme', savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const target = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', target);
      localStorage.setItem('radar_theme', target);
    });
  }

  // Quick Filter Chips (Today/Index page)
  const filterChips = document.querySelectorAll('.filter-chip');
  const cards = document.querySelectorAll('.radar-card');

  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const filterType = chip.getAttribute('data-filter');

      cards.forEach(card => {
        const cardType = card.getAttribute('data-type');
        if (filterType === 'all' || cardType === filterType) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });

  // Client-side Search (Search page)
  const searchInput = document.getElementById('search-input');
  const clearBtn = document.getElementById('search-clear');
  const typeFilter = document.getElementById('filter-type');
  const sortFilter = document.getElementById('filter-sort');
  const searchCards = document.querySelectorAll('.search-card');
  const resultsCount = document.getElementById('results-count');

  function runSearch() {
    if (!searchInput) return;
    const query = searchInput.value.toLowerCase().trim();
    const selectedType = typeFilter ? typeFilter.value : '';
    let visibleCount = 0;

    searchCards.forEach(card => {
      const title = (card.querySelector('.card-title') || {}).innerText?.toLowerCase() || '';
      const summary = (card.querySelector('.card-summary') || {}).innerText?.toLowerCase() || '';
      const topics = (card.getAttribute('data-topics') || '').toLowerCase();
      const cardType = card.getAttribute('data-type') || '';

      const matchesQuery = !query || title.includes(query) || summary.includes(query) || topics.includes(query);
      const matchesType = !selectedType || cardType === selectedType;

      if (matchesQuery && matchesType) {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    if (resultsCount) {
      resultsCount.innerText = visibleCount;
    }
  }

  if (searchInput) {
    searchInput.addEventListener('input', runSearch);
  }
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      runSearch();
    });
  }
  if (typeFilter) {
    typeFilter.addEventListener('change', runSearch);
  }

  // Bookmarking in Client LocalStorage
  const bookmarkButtons = document.querySelectorAll('.bookmark-btn');
  let savedBookmarks = JSON.parse(localStorage.getItem('radar_client_bookmarks') || '{}');

  function updateBookmarkUI() {
    bookmarkButtons.forEach(btn => {
      const uid = btn.getAttribute('data-uid');
      if (savedBookmarks[uid]) {
        btn.innerText = '★ Bookmarked';
        btn.classList.add('btn-bookmarked');
      } else {
        btn.innerText = '⭐ Bookmark';
        btn.classList.remove('btn-bookmarked');
      }
    });
  }

  bookmarkButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const uid = btn.getAttribute('data-uid');
      const title = btn.getAttribute('data-title');
      if (savedBookmarks[uid]) {
        delete savedBookmarks[uid];
      } else {
        savedBookmarks[uid] = { title, savedAt: new Date().toISOString() };
      }
      localStorage.setItem('radar_client_bookmarks', JSON.stringify(savedBookmarks));
      updateBookmarkUI();
    });
  });

  updateBookmarkUI();
});
