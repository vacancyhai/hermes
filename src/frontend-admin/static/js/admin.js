/**
 * admin.js — Hermes Admin Frontend
 *
 * Responsibilities:
 *  - Sidebar mobile toggle
 *  - Flash message auto-dismiss and manual close
 *  - Confirm dialogs for destructive actions
 */

(function () {
  'use strict';

  /* ── Sidebar mobile toggle ─────────────────────────────── */
  var toggleBtn = document.getElementById('sidebar-toggle');
  var sidebar   = document.getElementById('sidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('sidebar--open');
    });

    // Close sidebar when clicking outside of it on mobile
    document.addEventListener('click', function (e) {
      if (
        sidebar.classList.contains('sidebar--open') &&
        !sidebar.contains(e.target) &&
        e.target !== toggleBtn
      ) {
        sidebar.classList.remove('sidebar--open');
      }
    });
  }

  /* ── Flash message handling ────────────────────────────── */
  var FLASH_DELAY_MS = 6000;

  document.querySelectorAll('.flash__item').forEach(function (item) {
    var closeBtn = item.querySelector('.flash__close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        dismissFlash(item);
      });
    }

    if (!item.classList.contains('flash__item--error')) {
      setTimeout(function () { dismissFlash(item); }, FLASH_DELAY_MS);
    }
  });

  function dismissFlash(el) {
    el.style.transition = 'opacity 0.3s';
    el.style.opacity    = '0';
    setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 300);
  }

  /* ── Confirm dialogs ───────────────────────────────────── */
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      var msg = el.dataset.confirm || 'Are you sure?';
      if (!window.confirm(msg)) {
        e.preventDefault();
      }
    });
  });
})();
