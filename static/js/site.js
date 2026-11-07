/* Ostia Management - motion layer.
   Vanilla, progressive, and silent when the visitor prefers reduced motion. */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  function on(el, ev, fn, opts) {
    if (el) el.addEventListener(ev, fn, opts);
  }

  /* Shared observer: adds .is-in once, then stops watching.
     `proxy` lets us observe a different node than the one we mark. An element
     that clips itself to nothing (data-clip) reports zero intersection area, so
     it can never trigger its own reveal - we watch its parent instead. */
  var seen = null;
  var marks = typeof Map === "function" ? new Map() : null;

  function watch(el, proxy) {
    if (!el) return;
    if (reduced || !("IntersectionObserver" in window) || !marks) {
      el.classList.add("is-in");
      return;
    }
    var target = proxy || el;

    if (!seen) {
      seen = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            (marks.get(entry.target) || [entry.target]).forEach(function (node) {
              node.classList.add("is-in");
            });
            seen.unobserve(entry.target);
            marks.delete(entry.target);
          });
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
      );
    }

    var list = marks.get(target);
    if (list) {
      if (list.indexOf(el) === -1) list.push(el);
      return;
    }
    marks.set(target, [el]);
    seen.observe(target);
  }

  /* ---------- Headline word-by-word reveal ---------- */
  function splitHeadings() {
    document.querySelectorAll("[data-split]").forEach(function (el) {
      if (el.dataset.splitDone) return;
      el.dataset.splitDone = "1";

      // Walk top-level nodes so inline <span class="mark"> keeps its colour.
      var out = [];
      var index = 0;

      function pushWords(text, className) {
        text.split(/(\s+)/).forEach(function (chunk) {
          if (!chunk.trim()) {
            out.push(" ");
            return;
          }
          var cls = className ? ' class="' + className + '"' : "";
          out.push(
            '<span class="word"><span style="--i:' + index + '"' + cls + ">" + chunk + "</span></span>"
          );
          index += 1;
        });
      }

      Array.prototype.forEach.call(el.childNodes, function (node) {
        if (node.nodeType === 3) {
          pushWords(node.textContent, "");
        } else if (node.nodeType === 1) {
          pushWords(node.textContent, node.className);
        }
      });

      el.innerHTML = out.join("");
      watch(el);
    });
  }

  /* ---------- SVG doodles draw themselves ---------- */
  function doodles() {
    document.querySelectorAll("[data-draw]").forEach(function (svg) {
      svg.querySelectorAll("path").forEach(function (path) {
        var len = 400;
        try {
          len = Math.ceil(path.getTotalLength()) || 400;
        } catch (e) {
          /* getTotalLength can throw on a detached node; the default is fine */
        }
        path.style.setProperty("--len", len);
      });
      watch(svg);
    });
  }

  /* ---------- Sticky header + scroll progress ---------- */
  function scrollChrome() {
    var header = document.querySelector(".site-header");
    var bar = document.querySelector(".scroll-progress");
    if (!header && !bar) return;

    function update() {
      if (header) header.classList.toggle("is-stuck", window.scrollY > 8);
      if (bar) {
        var max = document.documentElement.scrollHeight - window.innerHeight;
        var ratio = max > 0 ? window.scrollY / max : 0;
        bar.style.transform = "scaleX(" + Math.min(1, Math.max(0, ratio)) + ")";
      }
    }
    update();
    on(window, "scroll", update, { passive: true });
    on(window, "resize", update);
  }

  /* ---------- Mobile drawer ---------- */
  function drawer() {
    var toggle = document.querySelector(".nav-toggle");
    var panel = document.querySelector(".drawer");
    if (!toggle || !panel) return;

    function setOpen(open) {
      toggle.setAttribute("aria-expanded", String(open));
      panel.classList.toggle("is-open", open);
      document.body.style.overflow = open ? "hidden" : "";
    }

    on(toggle, "click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    on(document, "keydown", function (e) {
      if (e.key === "Escape") setOpen(false);
    });
    panel.querySelectorAll("a").forEach(function (a) {
      on(a, "click", function () {
        setOpen(false);
      });
    });
  }

  /* ---------- Count-up numbers ---------- */
  function counters() {
    var nodes = document.querySelectorAll("[data-count]");
    if (!nodes.length) return;

    function run(el) {
      var raw = el.getAttribute("data-count") || "";
      var match = raw.match(/-?[\d.,]+/);
      if (!match || reduced) {
        el.textContent = raw;
        return;
      }
      var numeric = match[0];
      var target = parseFloat(numeric.replace(/,/g, ""));
      if (isNaN(target)) {
        el.textContent = raw;
        return;
      }
      var decimals = (numeric.split(".")[1] || "").length;
      var grouped = numeric.indexOf(",") > -1;
      var prefix = raw.slice(0, match.index);
      var suffix = raw.slice(match.index + numeric.length);
      var started = null;

      function frame(now) {
        if (started === null) started = now;
        var p = Math.min(1, (now - started) / 1500);
        var value = target * (1 - Math.pow(1 - p, 3));
        var text = decimals ? value.toFixed(decimals) : String(Math.round(value));
        if (grouped) text = Number(text).toLocaleString("en-GB");
        el.textContent = prefix + text + suffix;
        if (p < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    }

    if (!("IntersectionObserver" in window)) {
      nodes.forEach(run);
      return;
    }
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          run(entry.target);
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.4 }
    );
    nodes.forEach(function (el) {
      io.observe(el);
    });
  }

  /* ---------- Marquee: duplicate the track for a seamless loop ---------- */
  function marquee() {
    document.querySelectorAll(".strip__track").forEach(function (track) {
      track.innerHTML += track.innerHTML;
    });
  }

  /* ---------- Parallax: framed photos drift, float cards counter-drift ---------- */
  function parallax() {
    var layers = document.querySelectorAll("[data-par]");
    if (!layers.length || reduced) return;
    var ticking = false;

    function update() {
      var vh = window.innerHeight;
      layers.forEach(function (el) {
        var rect = el.getBoundingClientRect();
        if (rect.bottom < -200 || rect.top > vh + 200) return;
        // -1 .. 1 across the viewport
        var progress = (rect.top + rect.height / 2 - vh / 2) / vh;
        var depth = parseFloat(el.getAttribute("data-par")) || 0.1;
        el.style.transform = "translate3d(0," + progress * depth * -100 + "px,0)";
      });
      ticking = false;
    }

    on(
      window,
      "scroll",
      function () {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(update);
      },
      { passive: true }
    );
    update();
  }

  /* ---------- Magnetic buttons ---------- */
  function magnetic() {
    if (reduced || !fine) return;
    document.querySelectorAll("[data-magnetic]").forEach(function (btn) {
      on(btn, "pointermove", function (e) {
        var r = btn.getBoundingClientRect();
        var dx = e.clientX - (r.left + r.width / 2);
        var dy = e.clientY - (r.top + r.height / 2);
        btn.style.transform = "translate(" + dx * 0.18 + "px," + (dy * 0.18 - 3) + "px)";
      });
      on(btn, "pointerleave", function () {
        btn.style.transform = "";
      });
    });
  }

  /* ---------- Tabs ---------- */
  function tabs() {
    document.querySelectorAll("[data-tabs]").forEach(function (group) {
      var buttons = group.querySelectorAll(".tabs__btn");
      var panels = group.querySelectorAll(".tabs__panel");
      buttons.forEach(function (btn, i) {
        on(btn, "click", function () {
          buttons.forEach(function (b) {
            b.setAttribute("aria-selected", "false");
          });
          panels.forEach(function (p) {
            p.classList.remove("is-active");
          });
          btn.setAttribute("aria-selected", "true");
          if (panels[i]) panels[i].classList.add("is-active");
        });
      });
    });
  }

  /* ---------- FAQ accordion ---------- */
  function faq() {
    document.querySelectorAll(".faq__item").forEach(function (item) {
      var btn = item.querySelector(".faq__q");
      var body = item.querySelector(".faq__a");
      if (!btn || !body) return;

      on(btn, "click", function () {
        var open = item.classList.contains("is-open");
        // One panel at a time, so the column never jumps around.
        var group = item.closest(".faq");
        if (group) {
          group.querySelectorAll(".faq__item.is-open").forEach(function (other) {
            if (other === item) return;
            other.classList.remove("is-open");
            var ob = other.querySelector(".faq__q");
            var oa = other.querySelector(".faq__a");
            if (ob) ob.setAttribute("aria-expanded", "false");
            if (oa) oa.style.height = "0px";
          });
        }
        item.classList.toggle("is-open", !open);
        btn.setAttribute("aria-expanded", String(!open));
        body.style.height = open ? "0px" : body.scrollHeight + "px";
      });
    });

    on(window, "resize", function () {
      document.querySelectorAll(".faq__item.is-open .faq__a").forEach(function (body) {
        body.style.height = body.scrollHeight + "px";
      });
    });
  }

  /* ---------- Process track progress ---------- */
  function track() {
    document.querySelectorAll(".track").forEach(function (row) {
      var fill = row.querySelector(".track__fill");
      var steps = row.querySelectorAll(".track__step");
      if (!steps.length) return;

      function update() {
        var rect = row.getBoundingClientRect();
        var mid = window.innerHeight * 0.62;
        var lit = 0;
        steps.forEach(function (step) {
          var on = step.getBoundingClientRect().top < mid;
          step.classList.toggle("is-lit", on);
          if (on) lit += 1;
        });
        if (fill && rect.height) {
          fill.style.width = (lit / steps.length) * 100 + "%";
        }
      }
      update();
      on(window, "scroll", update, { passive: true });
      on(window, "resize", update);
    });
  }

  /* ---------- Certification cycle: the diagram follows the step being read ----------
     Everything shows fully lit until .is-live is added, so no script, reduced motion and
     narrow screens (where the diagram is not sticky) all get the complete picture. */
  function cycle() {
    if (reduced) return;
    var wide = window.matchMedia("(min-width: 921px)");
    document.querySelectorAll("[data-cycle]").forEach(function (root) {
      var steps = root.querySelectorAll(".cycle__step");
      var marks = root.querySelectorAll("[data-upto]");
      var phase = root.querySelector("[data-cycle-phase]");
      var count = root.querySelector("[data-cycle-count]");
      var resting = phase.textContent;
      var current = 0;

      function update() {
        if (!wide.matches) {
          root.classList.remove("is-live");
          phase.textContent = resting;
          count.textContent = "";
          current = 0;
          return;
        }
        var line = window.innerHeight * 0.55;
        var now = 1;
        steps.forEach(function (step, i) {
          if (step.getBoundingClientRect().top < line) now = i + 1;
        });
        if (now === current) return;
        current = now;
        root.classList.add("is-live");
        steps.forEach(function (step, i) {
          step.classList.toggle("is-now", i + 1 === now);
          step.classList.toggle("is-lit", i + 1 <= now);
        });
        marks.forEach(function (mark) {
          var upto = Number(mark.getAttribute("data-upto"));
          mark.classList.toggle("is-lit", upto <= now);
          mark.classList.toggle("is-now", upto === now);
        });
        phase.textContent = steps[now - 1].getAttribute("data-phase") || resting;
        count.textContent = (root.getAttribute("data-counter") || "")
          .replace("{n}", now)
          .replace("{total}", steps.length);
      }
      update();
      on(window, "scroll", update, { passive: true });
      on(window, "resize", update);
    });
  }

  /* ---------- Standards filter ---------- */
  function filters() {
    var bar = document.querySelector("[data-filter-bar]");
    if (!bar) return;
    var cards = document.querySelectorAll("[data-category]");
    bar.querySelectorAll(".filter-btn").forEach(function (btn) {
      on(btn, "click", function () {
        var key = btn.getAttribute("data-filter");
        bar.querySelectorAll(".filter-btn").forEach(function (b) {
          b.setAttribute("aria-pressed", String(b === btn));
        });
        cards.forEach(function (card) {
          var show = key === "all" || card.getAttribute("data-category") === key;
          card.classList.toggle("is-hidden", !show);
        });
      });
    });
  }

  /* ---------- Boot ---------- */
  function init() {
    marquee();
    splitHeadings();
    doodles();
    document.querySelectorAll("[data-reveal], .float-card").forEach(function (el) {
      watch(el);
    });
    // Clipped elements are revealed off their parent's visibility.
    document.querySelectorAll("[data-clip]").forEach(function (el) {
      watch(el, el.parentElement || el);
    });
    scrollChrome();
    drawer();
    counters();
    parallax();
    magnetic();
    tabs();
    faq();
    track();
    cycle();
    filters();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
