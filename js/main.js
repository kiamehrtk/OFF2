/**
 * OFF2 Homepage — behavior
 * Ported from the design's <script data-dc-script> logic (hero carousel +
 * scroll-reveal), plus a small nav toggle and newsletter stub that the
 * source design didn't need to handle itself.
 */
(function () {
  'use strict';

  var AUTOPLAY_MS = 6000; // matches the design's default autoplaySeconds (6)

  /* ---------- Hero carousel ---------- */
  function initHero() {
    var slides = Array.prototype.slice.call(document.querySelectorAll('[data-hero-slide]'));
    var dots = Array.prototype.slice.call(document.querySelectorAll('[data-hero-dot]'));
    var counter = document.getElementById('hero-counter');
    var prevBtn = document.getElementById('hero-prev');
    var nextBtn = document.getElementById('hero-next');
    var hero = document.getElementById('top');
    if (!slides.length) return;

    var index = 0;
    var timer = null;

    function go(n) {
      index = (n + slides.length) % slides.length;
      slides.forEach(function (s, i) { s.classList.toggle('is-active', i === index); });
      dots.forEach(function (d, i) { d.classList.toggle('is-active', i === index); });
      if (counter) {
        counter.textContent = String(index + 1).padStart(2, '0') + ' / ' + String(slides.length).padStart(2, '0');
      }
    }

    function stop() { if (timer) clearInterval(timer); }
    function restart() {
      stop();
      timer = setInterval(function () { go(index + 1); }, AUTOPLAY_MS);
    }

    dots.forEach(function (d, i) {
      d.addEventListener('click', function () { go(i); restart(); });
    });
    if (prevBtn) prevBtn.addEventListener('click', function () { go(index - 1); restart(); });
    if (nextBtn) nextBtn.addEventListener('click', function () { go(index + 1); restart(); });
    if (hero) {
      hero.addEventListener('mouseenter', stop);
      hero.addEventListener('mouseleave', restart);
    }

    go(0);
    restart();
  }

  /* ---------- Scroll reveal ---------- */
  function initReveal() {
    var targets = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));
    if (!targets.length) return;

    if (!('IntersectionObserver' in window)) {
      targets.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });

    targets.forEach(function (el) { io.observe(el); });

    // Fallback: if something never intersects (e.g. hidden ancestor), reveal
    // everything after 2s so content is never stuck invisible.
    setTimeout(function () {
      targets.forEach(function (el) { el.classList.add('is-visible'); });
    }, 2000);
  }

  /* ---------- Mobile nav toggle ---------- */
  function initNav() {
    var nav = document.getElementById('site-nav');
    var toggle = document.getElementById('nav-toggle');
    if (!nav || !toggle) return;
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.querySelectorAll('.nav__links a').forEach(function (a) {
      a.addEventListener('click', function () {
        nav.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ---------- Filter groups (events.html venues, gallery.html albums) ----------
   * Any element with [data-filter-group] wraps a set of [data-filter-btn]
   * buttons and the [data-filter-key] items they show/hide. A button with
   * value "all" matches everything. An optional [data-filter-empty="<key>"]
   * inside the group is revealed when that key matches nothing.
   */
  var FILTER_FADE_MS = 260; // keep in sync with .is-filtered-out transition

  function initFilterGroups() {
    var groups = Array.prototype.slice.call(document.querySelectorAll('[data-filter-group]'));

    groups.forEach(function (group) {
      var buttons = Array.prototype.slice.call(group.querySelectorAll('[data-filter-btn]'));
      var items = Array.prototype.slice.call(group.querySelectorAll('[data-filter-key]'));
      var empties = Array.prototype.slice.call(group.querySelectorAll('[data-filter-empty]'));
      if (!buttons.length || !items.length) return;

      function apply(key) {
        var visible = 0;
        items.forEach(function (item) {
          var match = key === 'all' || item.getAttribute('data-filter-key') === key;
          if (match) {
            visible++;
            item.style.display = '';
            // Next frame so display:'' lands before the class is removed —
            // otherwise there's no starting value to transition from and the
            // fade-in is skipped.
            requestAnimationFrame(function () { item.classList.remove('is-filtered-out'); });
          } else {
            item.classList.add('is-filtered-out');
            setTimeout(function () {
              if (item.classList.contains('is-filtered-out')) item.style.display = 'none';
            }, FILTER_FADE_MS);
          }
        });

        empties.forEach(function (el) {
          el.classList.toggle('is-visible', visible === 0 && el.getAttribute('data-filter-empty') === key);
        });
      }

      buttons.forEach(function (btn) {
        btn.addEventListener('click', function () {
          buttons.forEach(function (b) {
            b.classList.remove('is-active');
            b.setAttribute('aria-pressed', 'false');
          });
          btn.classList.add('is-active');
          btn.setAttribute('aria-pressed', 'true');
          apply(btn.getAttribute('data-filter-btn'));
        });
      });
    });
  }

  /* ---------- Lightbox (gallery.html) ---------- */
  function initLightbox() {
    var triggers = Array.prototype.slice.call(document.querySelectorAll('[data-lightbox]'));
    var box = document.getElementById('lightbox');
    if (!triggers.length || !box) return;

    var figure = box.querySelector('.lightbox__figure');
    var caption = box.querySelector('.lightbox__caption');
    var closeBtn = box.querySelector('.lightbox__close');
    var lastFocused = null;

    function open(trigger) {
      lastFocused = trigger;
      var img = trigger.querySelector('img');
      var text = trigger.getAttribute('data-lightbox') || '';
      // Real photo when one exists, otherwise mirror the placeholder tile so
      // the lightbox never opens onto an empty frame.
      figure.innerHTML = img
        ? '<img src="' + img.getAttribute('src') + '" alt="' + (img.getAttribute('alt') || '') + '">'
        : '<div class="lightbox__placeholder">Image not uploaded yet</div>';
      caption.textContent = text;
      box.classList.add('is-open');
      box.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      closeBtn.focus();
    }

    function close() {
      box.classList.remove('is-open');
      box.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
      if (lastFocused) lastFocused.focus();
    }

    triggers.forEach(function (t) {
      t.addEventListener('click', function (e) { e.preventDefault(); open(t); });
    });
    closeBtn.addEventListener('click', close);
    box.addEventListener('click', function (e) { if (e.target === box) close(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && box.classList.contains('is-open')) close();
    });
  }

  /* ---------- Newsletter form (stub — wire to real provider later) ---------- */
  function initNewsletter() {
    var form = document.getElementById('newsletter-form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var input = form.querySelector('input[type="email"]');
      var btn = form.querySelector('button');
      if (!input || !input.value) return;
      var original = btn.textContent;
      btn.textContent = 'Thanks!';
      btn.disabled = true;
      input.value = '';
      setTimeout(function () { btn.textContent = original; btn.disabled = false; }, 2500);
      // TODO: replace with a real signup endpoint (Mailchimp/Klaviyo/etc.)
      // once the CMS/marketing stack is chosen.
    });
  }

  function safe(fn, name) {
    try { fn(); } catch (e) { console.error('[off2] ' + name + ' failed:', e); }
  }

  function init() {
    safe(initHero, 'initHero');
    safe(initReveal, 'initReveal');
    safe(initNav, 'initNav');
    safe(initFilterGroups, 'initFilterGroups');
    safe(initLightbox, 'initLightbox');
    safe(initNewsletter, 'initNewsletter');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
