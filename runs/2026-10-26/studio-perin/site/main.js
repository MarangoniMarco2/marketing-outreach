(function () {
  var doc = document.documentElement;

  /* ---- Siete aperti adesso? (Google Maps hours, Europe/Rome) ---- */
  var HOURS = { 1: [510, 1140], 2: [600, 1140], 3: [510, 1140], 4: [600, 1140], 5: [510, 930] };
  var NAMES = ['domenica', 'lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato'];
  function fmt(m) { return Math.floor(m / 60) + ':' + ('0' + (m % 60)).slice(-2); }
  function romeNow() {
    try {
      var parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Rome', weekday: 'short', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(new Date());
      var o = {}; parts.forEach(function (p) { o[p.type] = p.value; });
      var day = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(o.weekday);
      return { day: day, min: (parseInt(o.hour, 10) % 24) * 60 + parseInt(o.minute, 10) };
    } catch (e) { var d = new Date(); return { day: d.getDay(), min: d.getHours() * 60 + d.getMinutes() }; }
  }
  function status() {
    var n = romeNow(), h = HOURS[n.day];
    if (h && n.min >= h[0] && n.min < h[1]) return 'Adesso siamo aperti, fino alle ' + fmt(h[1]) + '.';
    if (h && n.min < h[0]) return 'Adesso siamo chiusi. Oggi apriamo alle ' + fmt(h[0]) + '.';
    for (var i = 1; i <= 7; i++) {
      var d = (n.day + i) % 7;
      if (HOURS[d]) return 'Adesso siamo chiusi. Riapriamo ' + (i === 1 ? 'domani' : NAMES[d]) + ' alle ' + fmt(HOURS[d][0]) + '.';
    }
    return '';
  }
  function paint() {
    var s = status();
    document.querySelectorAll('[data-now]').forEach(function (el) { if (s) el.textContent = s; });
    var n = romeNow();
    document.querySelectorAll('.hours tr').forEach(function (tr) {
      var d = parseInt(tr.getAttribute('data-day'), 10);
      tr.classList.toggle('today', d === n.day || (d === 6 && (n.day === 0 || n.day === 6)));
    });
  }
  paint();
  setInterval(paint, 60000);

  /* ---- menu on phones ---- */
  var menu = document.getElementById('menu'), links = document.getElementById('links');
  menu.addEventListener('click', function () {
    var open = links.classList.toggle('open');
    menu.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  links.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') { links.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); }
  });

  /* ---- the bar takes the colour of the chapter under it ---- */
  var GROUNDS = {
    bg: ['#eeede8', '#12333a', '#12333a', '#eeede8'],
    surface: ['#e2e1da', '#12333a', '#12333a', '#eeede8'],
    field: ['#9bbac2', '#0c262b', '#0c262b', '#eeede8'],
    deep: ['#12333a', '#eeede8', '#eeede8', '#12333a'],
    mid: ['#2a6470', '#f3f2ee', '#f3f2ee', '#12333a']
  };
  var bar = document.getElementById('bar');
  var chapters = Array.prototype.slice.call(document.querySelectorAll('[data-ground]'));
  function setBar() {
    var y = bar.offsetHeight / 2, g = 'bg';
    for (var i = 0; i < chapters.length; i++) {
      var r = chapters[i].getBoundingClientRect();
      if (r.top <= y && r.bottom > y) { g = chapters[i].getAttribute('data-ground'); break; }
    }
    var c = GROUNDS[g] || GROUNDS.bg;
    bar.style.setProperty('--bar-bg', c[0]);
    bar.style.setProperty('--bar-ink', c[1]);
    bar.style.setProperty('--bar-btn', c[2]);
    bar.style.setProperty('--bar-btn-ink', c[3]);
  }
  setBar();
  window.addEventListener('scroll', setBar, { passive: true });

  /* ---- entrances: never hide what is already on screen; show all if anything odd happens ---- */
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!('IntersectionObserver' in window) || reduce) return;
  var items = Array.prototype.slice.call(document.querySelectorAll('.reveal'));
  var vh = window.innerHeight;
  doc.classList.add('js');
  items.forEach(function (el) {
    var sib = el.parentElement ? Array.prototype.indexOf.call(el.parentElement.querySelectorAll(':scope > .reveal'), el) : 0;
    el.style.setProperty('--d', Math.max(0, sib) * 80 + 'ms');
    if (el.getBoundingClientRect().top < vh) el.classList.add('in');
  });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -8% 0px' });
  items.forEach(function (el) { if (!el.classList.contains('in')) io.observe(el); });
  function showAll() { items.forEach(function (el) { el.classList.add('in'); }); }
  window.addEventListener('resize', function () { if (Math.abs(window.innerHeight - vh) > 200) showAll(); });
  window.addEventListener('beforeprint', showAll);
})();
