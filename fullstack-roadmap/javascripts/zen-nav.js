/* ==========================================================================
   Zen Reading Mode & Hamburger Module Navigator
   Provides clean reading view by hiding bulky headers and offering
   a top-left 3-bar (hamburger) dropdown to switch between modules.
   ========================================================================== */

(function () {
  function initZenNav() {
    var primarySidebar = document.querySelector('.md-sidebar--primary');
    var isLandingPage = !primarySidebar || primarySidebar.hasAttribute('hidden');

    if (isLandingPage) {
      document.body.classList.remove('zen-mode');
      var oldWidget = document.getElementById('zen-nav');
      if (oldWidget) oldWidget.remove();
      return;
    }

    document.body.classList.add('zen-mode');

    // If widget already exists, update its active module title
    var existingWidget = document.getElementById('zen-nav');
    if (existingWidget) {
      updateActiveModule(existingWidget);
      return;
    }

    // Read tabs from original MkDocs DOM to extract exact relative URLs
    var tabLinks = document.querySelectorAll('.md-tabs__link');
    var modules = [];
    var activeTitle = 'Module';

    var moduleIcons = {
      'trang chủ': '🏠',
      'hướng dẫn': '🧭',
      'lộ trình': '🧭',
      'c nền tảng': '🇨',
      'c · nền tảng': '🇨',
      '01': '🇨',
      'c chuyên sâu': '🧠',
      'c · chuyên sâu': '🧠',
      '02': '🧠',
      'c++': '⚡',
      '03': '⚡',
      'c# cơ bản': '🔷',
      'c# · cơ bản': '🔷',
      '04': '🔷',
      'c# nâng cao': '🚀',
      'c# · nâng cao': '🚀',
      '05': '🚀',
      'oop': '📐',
      '06': '📐'
    };

    function getCleanTitleAndIcon(rawTitle) {
      var trimmed = rawTitle.trim();
      var icon = '📚';
      // If title starts with emoji, extract it
      var match = trimmed.match(/^([\p{Extended_Pictographic}\uD800-\uDBFF\uDC00-\uDFFF\u2600-\u27BF]+)\s*(.*)$/u);
      if (match) {
        icon = match[1];
        trimmed = match[2];
      } else {
        var lower = trimmed.toLowerCase();
        for (var key in moduleIcons) {
          if (lower.indexOf(key) !== -1) {
            icon = moduleIcons[key];
            break;
          }
        }
      }
      return { title: trimmed, icon: icon };
    }

    tabLinks.forEach(function (link) {
      var rawTitle = link.textContent.trim();
      var parsed = getCleanTitleAndIcon(rawTitle);
      var href = link.getAttribute('href');
      var itemParent = link.closest('.md-tabs__item');
      var isActive = link.classList.contains('md-tabs__link--active') || 
                     (itemParent && itemParent.classList.contains('md-tabs__item--active'));
      if (isActive) {
        activeTitle = parsed.title;
      }
      modules.push({
        title: parsed.title,
        href: href,
        isActive: isActive,
        icon: parsed.icon
      });
    });

    // Build the Zen Nav Widget
    var navContainer = document.createElement('div');
    navContainer.id = 'zen-nav';
    navContainer.className = 'zen-nav';

    var triggerBtn = document.createElement('button');
    triggerBtn.className = 'zen-nav__trigger';
    triggerBtn.setAttribute('aria-label', 'Menu Lựa chọn Module');
    triggerBtn.innerHTML =
      '<div class="zen-nav__bars"><span></span><span></span><span></span></div>' +
      '<span class="zen-nav__title">' + (activeTitle || 'Danh mục Module') + '</span>' +
      '<svg class="zen-nav__arrow" viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>';

    var dropdown = document.createElement('div');
    dropdown.className = 'zen-nav__dropdown';

    // Dropdown header
    var headerHtml =
      '<div class="zen-nav__dropdown-header">' +
        '<div class="zen-nav__brand">' +
          '<span class="zen-nav__brand-badge">Full-stack Roadmap</span>' +
          '<div class="zen-nav__brand-title">Lựa chọn Module Học</div>' +
        '</div>' +
        '<div class="zen-nav__actions">' +
          '<button type="button" class="zen-action-btn" id="zen-search-action" title="Tìm kiếm bài học">' +
            '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/></svg>' +
          '</button>' +
          '<button type="button" class="zen-action-btn" id="zen-palette-action" title="Đổi giao diện Sáng/Tối">' +
            '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 2A10 10 0 0 0 2 12A10 10 0 0 0 12 22A10 10 0 0 0 22 12A10 10 0 0 0 12 2M12 4A8 8 0 0 1 20 12A8 8 0 0 1 12 20V4Z"/></svg>' +
          '</button>' +
        '</div>' +
      '</div>';

    // Module list
    var listHtml = '<div class="zen-nav__grid">';
    modules.forEach(function (mod) {
      var activeCls = mod.isActive ? ' is-active' : '';
      listHtml +=
        '<a href="' + mod.href + '" class="zen-nav__item' + activeCls + '">' +
          '<span class="zen-nav__item-icon">' + mod.icon + '</span>' +
          '<div class="zen-nav__item-text">' +
            '<span class="zen-nav__item-name">' + mod.title + '</span>' +
          '</div>' +
          (mod.isActive ? '<span class="zen-nav__item-dot"></span>' : '') +
        '</a>';
    });
    listHtml += '</div>';

    dropdown.innerHTML = headerHtml + listHtml;

    navContainer.appendChild(triggerBtn);
    navContainer.appendChild(dropdown);
    document.body.appendChild(navContainer);

    // Toggle menu on click
    triggerBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      navContainer.classList.toggle('is-open');
    });

    // Close when clicking outside
    document.addEventListener('click', function (e) {
      if (!navContainer.contains(e.target)) {
        navContainer.classList.remove('is-open');
      }
    });

    // Search action click
    var searchBtn = dropdown.querySelector('#zen-search-action');
    if (searchBtn) {
      searchBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        navContainer.classList.remove('is-open');
        var searchInput = document.querySelector('.md-search__input');
        if (searchInput) {
          searchInput.focus();
        } else {
          var searchLabel = document.querySelector('label[for="__search"]');
          if (searchLabel) searchLabel.click();
        }
      });
    }

    // Palette theme switch
    var paletteBtn = dropdown.querySelector('#zen-palette-action');
    if (paletteBtn) {
      paletteBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        var paletteInput = document.querySelector('form[data-md-component="palette"] input[name="__palette"]:not(:checked)');
        if (paletteInput) {
          paletteInput.click();
        }
      });
    }
  }

  function updateActiveModule(container) {
    var tabLinks = document.querySelectorAll('.md-tabs__link');
    tabLinks.forEach(function (link) {
      var itemParent = link.closest('.md-tabs__item');
      if (link.classList.contains('md-tabs__link--active') || (itemParent && itemParent.classList.contains('md-tabs__item--active'))) {
        var rawTitle = link.textContent.trim();
        var title = rawTitle.replace(/^[\p{Extended_Pictographic}\uD800-\uDBFF\uDC00-\uDFFF\u2600-\u27BF]+\s*/u, '');
        var titleEl = container.querySelector('.zen-nav__title');
        if (titleEl) titleEl.textContent = title;
      }
    });
  }

  if (typeof document$ !== 'undefined') {
    document$.subscribe(initZenNav);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initZenNav);
  } else {
    initZenNav();
  }
})();
