/**
 * notifications.js — in-app notification badge polling
 *
 * Polls the /notifications/count endpoint every 60 seconds and updates
 * the unread-count badge in the navbar.  No WebSocket / SSE required.
 *
 * Expected DOM element:
 *   <span id="notif-badge" data-hidden-class="notif-badge--hidden">0</span>
 *
 * Expected API endpoint (user frontend internal):
 *   GET /notifications/count  → { "unread_count": <int> }
 */

(function () {
  'use strict';

  var POLL_INTERVAL_MS = 60000; // 60 seconds
  var ENDPOINT         = '/notifications/count';

  var badge = document.getElementById('notif-badge');

  // Only activate when badge element and a logged-in context exist
  if (!badge) return;

  function updateBadge(count) {
    badge.textContent = count > 99 ? '99+' : String(count);
    var hiddenClass   = badge.dataset.hiddenClass || 'notif-badge--hidden';
    if (count > 0) {
      badge.classList.remove(hiddenClass);
      badge.setAttribute('aria-label', count + ' unread notifications');
    } else {
      badge.classList.add(hiddenClass);
      badge.setAttribute('aria-label', 'No unread notifications');
    }
  }

  function fetchCount() {
    fetch(ENDPOINT, {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (res) {
        if (!res.ok) return;
        return res.json();
      })
      .then(function (data) {
        if (data && typeof data.unread_count === 'number') {
          updateBadge(data.unread_count);
        }
      })
      .catch(function () {
        // Network error — silently ignore, badge keeps last value
      });
  }

  // Initial fetch on page load
  fetchCount();

  // Recurring poll
  setInterval(fetchCount, POLL_INTERVAL_MS);
})();
