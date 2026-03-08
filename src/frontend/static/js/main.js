/**
 * main.js — global utilities for the user-facing frontend
 *
 * Responsibilities:
 *  - Mobile navbar hamburger toggle
 *  - Flash message auto-dismiss (5s)
 *  - Active nav-link highlight from current URL
 */

(function () {
  'use strict';

  /* ── Navbar mobile toggle ──────────────────────────────────────────── */
  const hamburger = document.querySelector('.navbar__hamburger');
  const navMenu   = document.querySelector('.navbar__menu');

  if (hamburger && navMenu) {
    hamburger.addEventListener('click', function () {
      const expanded = hamburger.getAttribute('aria-expanded') === 'true';
      hamburger.setAttribute('aria-expanded', String(!expanded));
      navMenu.classList.toggle('navbar__menu--open');
    });

    // Close menu when a link inside it is clicked
    navMenu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navMenu.classList.remove('navbar__menu--open');
        hamburger.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ── Flash message auto-dismiss ───────────────────────────────────── */
  const FLASH_DELAY_MS = 5000;

  document.querySelectorAll('.flash__item').forEach(function (item) {
    // Manual dismiss button
    const closeBtn = item.querySelector('.flash__close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        dismissFlash(item);
      });
    }

    // Auto-dismiss (non-error messages only)
    if (!item.classList.contains('flash__item--error')) {
      setTimeout(function () {
        dismissFlash(item);
      }, FLASH_DELAY_MS);
    }
  });

  function dismissFlash(el) {
    el.style.transition = 'opacity 0.3s';
    el.style.opacity    = '0';
    setTimeout(function () {
      if (el.parentNode) {
        el.parentNode.removeChild(el);
      }
    }, 300);
  }

  /* ── Active nav-link ───────────────────────────────────────────────── */
  var currentPath = window.location.pathname;
  document.querySelectorAll('.navbar__link').forEach(function (link) {
    var href = link.getAttribute('href');
    if (href && currentPath.startsWith(href) && href !== '/') {
      link.classList.add('navbar__link--active');
    }
  });
})();
