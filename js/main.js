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

    var reduceMotion = window.matchMedia
      && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function showAll() {
      targets.forEach(function (el) { el.classList.add('is-visible'); });
    }

    if (reduceMotion || !('IntersectionObserver' in window)) {
      showAll();
      return;
    }

    // Stagger siblings so a row of cards arrives in sequence. Capped so a
    // long list never ends with an element waiting a noticeable beat.
    targets.forEach(function (el) {
      var parent = el.parentElement;
      if (!parent) return;
      var sibs = Array.prototype.filter.call(parent.children, function (c) {
        return c.hasAttribute('data-reveal');
      });
      var i = sibs.indexOf(el);
      if (i > 0) {
        el.style.setProperty('--reveal-delay', Math.min(i * 0.07, 0.28) + 's');
      }
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -8% 0px' });

    targets.forEach(function (el) { io.observe(el); });

    // Backstop. IntersectionObserver can stay silent in a document the
    // browser never renders (a background or occluded tab), which would
    // otherwise leave every section permanently invisible. This reveals
    // whatever is on screen from geometry alone, so the page degrades to
    // "content is simply there" rather than to a blank column. Scoped to
    // the viewport, so sections further down still animate on arrival.
    var pending = false;
    function revealInView() {
      pending = false;
      var remaining = targets.filter(function (el) {
        return !el.classList.contains('is-visible');
      });
      if (!remaining.length) {
        window.removeEventListener('scroll', onScroll);
        window.removeEventListener('resize', onScroll);
        return;
      }
      remaining.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.top < window.innerHeight * 0.92 && r.bottom > 0) {
          el.classList.add('is-visible');
          io.unobserve(el);
        }
      });
    }
    function onScroll() {
      if (pending) return;
      pending = true;
      window.requestAnimationFrame(revealInView);
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    setTimeout(revealInView, 2500);
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

  /* ---------- Demo submission form (label.html) ----------
     Posts to a form service (Formspree or equivalent) whose endpoint lives in
     the form's data-endpoint attribute. With no endpoint the form stays inert
     and disabled: a submission that goes nowhere must never show a success
     message. That is exactly the bug in initNewsletter above, and a producer
     who thinks their demo arrived when it did not is worse served than one who
     sees an honest error. */
  function initLabelForm() {
    var form = document.getElementById('demo-form');
    if (!form) return;

    var endpoint = (form.getAttribute('data-endpoint') || '').trim();
    var status = document.getElementById('demo-status');
    var button = form.querySelector('button[type="submit"]');
    var trap = form.querySelector('input[name="_gotcha"]');

    function say(message, kind) {
      if (!status) return;
      status.textContent = message;
      status.className = 'demo-form__status' + (kind ? ' is-' + kind : '');
    }

    // Not configured yet — leave every control disabled and do nothing.
    if (!endpoint) return;

    var fields = Array.prototype.slice.call(
      form.querySelectorAll('input, textarea')
    ).filter(function (el) { return el.name !== '_gotcha'; });
    fields.forEach(function (el) { el.disabled = false; });
    if (button) {
      button.disabled = false;
      button.textContent = 'Send demo';
    }
    var notice = form.querySelector('.demo-form__notice');
    if (notice && notice.parentNode) notice.parentNode.removeChild(notice);

    function invalid(el, message) {
      el.setAttribute('aria-invalid', 'true');
      say(message, 'error');
      el.focus();
      return false;
    }

    function validate() {
      fields.forEach(function (el) { el.removeAttribute('aria-invalid'); });

      var artist = form.querySelector('#demo-artist');
      var email = form.querySelector('#demo-email');
      var track = form.querySelector('#demo-title');
      var link = form.querySelector('#demo-link');

      if (!artist.value.trim()) return invalid(artist, 'Add your artist name.');
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
        return invalid(email, 'That email address does not look right.');
      }
      if (!track.value.trim()) return invalid(track, 'Add the track title.');

      var url = link.value.trim();
      if (!url) return invalid(link, 'Add a link to the track.');
      if (!/^https?:\/\//i.test(url)) {
        return invalid(link, 'The link needs to start with http:// or https://');
      }
      return true;
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      // Spam trap: people never see this field, so a filled one is a bot.
      // Show the normal success state rather than tipping it off.
      if (trap && trap.value) {
        form.innerHTML = '<p class="demo-form__status is-success">Thanks — we have your demo.</p>';
        return;
      }

      if (!validate()) return;

      var original = button ? button.textContent : '';
      if (button) { button.disabled = true; button.textContent = 'Sending…'; }
      say('', '');

      fetch(endpoint, {
        method: 'POST',
        headers: { Accept: 'application/json' },
        body: new FormData(form)
      }).then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        var track = form.querySelector('#demo-title').value.trim();
        form.innerHTML =
          '<p class="demo-form__status is-success">Thanks — we have &ldquo;' +
          track.replace(/[<>&"]/g, '') +
          '&rdquo;. We listen to everything, and you will hear back only if it is a fit. ' +
          'Allow four weeks.</p>';
      }).catch(function () {
        // Be honest and give them another route out.
        if (button) { button.disabled = false; button.textContent = original; }
        say('That did not send — something went wrong at our end. ' +
            'Please try again, or email us the link directly.', 'error');
      });
    });
  }

  function safe(fn, name) {
    try { fn(); } catch (e) { console.error('[off2] ' + name + ' failed:', e); }
  }

  /* ---------- Starfield behind the scrolling content ----------
     The pinned hero keeps the original .sky behind the carousel, but
     .page-flow is opaque and scrolls over it, so the stars and meteors would
     stop at the hero. Clone the node into the flow rather than repeating
     several hundred lines of inline gradients in the markup. */
  function initFlowSky() {
    var sky = document.querySelector('.hero-stack .sky');
    var flow = document.querySelector('.page-flow');
    if (!sky || !flow || flow.querySelector('.sky--flow')) return;

    var clone = sky.cloneNode(true);
    clone.classList.add('sky--flow');
    flow.insertBefore(clone, flow.firstChild);
  }

  function init() {
    safe(initHero, 'initHero');
    safe(initFlowSky, 'initFlowSky');
    safe(initReveal, 'initReveal');
    safe(initNav, 'initNav');
    safe(initFilterGroups, 'initFilterGroups');
    safe(initLightbox, 'initLightbox');
    safe(initNewsletter, 'initNewsletter');
    safe(initLabelForm, 'initLabelForm');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
