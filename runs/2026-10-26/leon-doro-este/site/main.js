(function () {
  var doc = document.documentElement;
  doc.classList.add('js');

  // Entrances: heading, then text, staggered, once.
  var items = Array.prototype.slice.call(document.querySelectorAll('.rv'));
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        var sibs = Array.prototype.slice.call(el.parentNode.querySelectorAll(':scope > .rv'));
        var i = Math.max(0, sibs.indexOf(el));
        el.style.transitionDelay = reduce ? '0ms' : (i * 80) + 'ms';
        el.classList.add('in');
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el) { io.observe(el); });
  }
  // Safety: never leave text hidden.
  setTimeout(function () { items.forEach(function (el) { el.classList.add('in'); }); }, 4000);

  // Siete aperti adesso? From the real Google hours (Europe/Rome).
  var days = ['domenica', 'lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato'];
  var slots = [[720, 840], [1170, 1290]]; // 12:00-14:00, 19:30-21:30, Mon to Sat
  function romeNow() {
    try {
      var parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Rome', weekday: 'short', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(new Date());
      var map = {};
      parts.forEach(function (p) { map[p.type] = p.value; });
      var wd = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(map.weekday);
      return { d: wd, m: (parseInt(map.hour, 10) % 24) * 60 + parseInt(map.minute, 10) };
    } catch (e) {
      var n = new Date();
      return { d: n.getDay(), m: n.getHours() * 60 + n.getMinutes() };
    }
  }
  function hhmm(m) { var h = Math.floor(m / 60), mm = m % 60; return h + ':' + (mm < 10 ? '0' : '') + mm; }
  function status() {
    var t = romeNow();
    if (t.d !== 0) {
      for (var i = 0; i < slots.length; i++) {
        if (t.m >= slots[i][0] && t.m < slots[i][1]) return 'La cucina è aperta adesso, fino alle ' + hhmm(slots[i][1]) + '.';
        if (t.m < slots[i][0]) return 'La cucina adesso è chiusa. Riapre oggi alle ' + hhmm(slots[i][0]) + '.';
      }
    }
    var next = (t.d + 1) % 7;
    if (next === 0) next = 1;
    var when = (next === (t.d + 1) % 7) ? 'domani' : days[next];
    return 'La cucina adesso è chiusa. Riapre ' + when + ' alle 12:00.';
  }
  var s = status();
  ['open-now', 'open-now-2'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.textContent = s;
  });

  // The coupon: builds the booking email the old site asked for.
  var form = document.getElementById('coupon');
  if (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var f = form.elements;
      var fmt = function (v) { if (!v) return ''; var p = v.split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : v; };
      var subject = 'Richiesta camera dal ' + fmt(f.arrivo.value) + ' al ' + fmt(f.partenza.value);
      var lines = [
        'Buongiorno,',
        'vorrei sapere se avete una camera libera.',
        '',
        'Nome e cognome: ' + f.nome.value,
        'Telefono: ' + f.telefono.value,
        'Arrivo: ' + fmt(f.arrivo.value),
        'Partenza: ' + fmt(f.partenza.value),
        'Adulti: ' + f.adulti.value,
        'Bambini: ' + f.bambini.value
      ];
      if (f.bici.checked) lines.push('Arriviamo in bici: ci serve il garage per le bici.');
      lines.push('', 'Grazie');
      window.location.href = 'mailto:prenotazioni@leondoroeste.it?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(lines.join('\n'));
    });
  }
})();
