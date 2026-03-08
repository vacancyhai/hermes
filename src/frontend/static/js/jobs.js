/**
 * jobs.js — job listing and detail page interactions
 *
 * Responsibilities:
 *  - Filter bar: auto-submit on select change (category, job_type, qualification)
 *  - Search debounce on text input (300ms) then form submit
 *  - Apply button confirmation dialog on detail page
 *  - Track / un-track button ARIA feedback
 */

(function () {
  'use strict';

  /* ── Filter bar auto-submit ────────────────────────────────────────── */
  const filterForm = document.getElementById('jobs-filter-form');

  if (filterForm) {
    // Auto-submit when a <select> changes
    filterForm.querySelectorAll('select').forEach(function (sel) {
      sel.addEventListener('change', function () {
        filterForm.submit();
      });
    });

    // Debounced submit for text search input
    var searchInput = filterForm.querySelector('input[name="q"]');
    if (searchInput) {
      var debounceTimer;
      searchInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () {
          filterForm.submit();
        }, 300);
      });
    }
  }

  /* ── Apply button confirmation ─────────────────────────────────────── */
  var applyForm = document.getElementById('apply-form');
  if (applyForm) {
    applyForm.addEventListener('submit', function (e) {
      var confirmed = window.confirm(
        'Submit your application for this position?'
      );
      if (!confirmed) {
        e.preventDefault();
      }
    });
  }

  /* ── Track button toggle ───────────────────────────────────────────── */
  var trackForm = document.getElementById('track-form');
  if (trackForm) {
    trackForm.addEventListener('submit', function () {
      var btn = trackForm.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Saving…';
      }
    });
  }
})();
