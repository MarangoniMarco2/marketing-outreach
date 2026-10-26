// Studio Pavin: open-now line, treatment tabs, appointment e-mail, quick bar colours.
(() => {
  // --- Siete aperti adesso? Hours from Google Maps: Mon-Fri 8:30-19:30, Europe/Rome.
  const days = ['domenica', 'lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato'];
  const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Europe/Rome' }));
  const d = now.getDay(), m = now.getHours() * 60 + now.getMinutes();
  const weekday = d >= 1 && d <= 5, open = weekday && m >= 510 && m < 1170;
  let text;
  if (open) {
    const left = 1170 - m;
    text = left <= 60 ? `Aperti adesso, ancora per ${left} minuti` : 'Aperti adesso, fino alle 19:30';
  } else if (weekday && m < 510) {
    text = 'Chiusi adesso, apriamo oggi alle 8:30';
  } else {
    let n = d, k = 0;
    do { n = (n + 1) % 7; k++; } while (n === 0 || n === 6);
    text = `Chiusi adesso, riapriamo ${k === 1 ? 'domani' : days[n]} alle 8:30`;
  }
  document.querySelectorAll('[data-open-now]').forEach((el) => {
    el.textContent = text;
    el.classList.add('open-now');
    el.classList.toggle('is-open', open);
  });

  // --- Appointment e-mail written from the chosen treatment
  const mail = (cura) => {
    const subject = cura ? `Richiesta appuntamento: ${cura}` : 'Richiesta appuntamento';
    const body = `Buongiorno,\nvorrei un appuntamento${cura ? ` per ${cura.toLowerCase()}` : ''}.\n\nNome e cognome:\nTelefono:\nGiorni e orari che preferisco:\n\nGrazie`;
    return `mailto:contatti@pavin.it?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };
  document.querySelectorAll('[data-cura]').forEach((a) => {
    a.href = mail(a.dataset.cura);
    a.setAttribute('aria-label', `Chiedi un appuntamento per ${a.dataset.cura}`);
  });

  // --- Tabs
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  const book = document.querySelector('[data-book]');
  const select = (tab, focus) => {
    tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute('aria-selected', on);
      t.tabIndex = on ? 0 : -1;
      const panel = document.getElementById(t.getAttribute('aria-controls'));
      panel.hidden = !on;
      if (on) panel.querySelectorAll('li').forEach((li, i) => { li.style.setProperty('--n', i); li.style.animation = 'none'; li.offsetWidth; li.style.animation = ''; });
    });
    if (book) { const area = tab.childNodes[0].textContent.trim(); book.href = mail(area); book.textContent = `Chiedi per ${area.toLowerCase()}`; }
    if (focus) tab.focus();
  };
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => select(t));
    t.addEventListener('keydown', (e) => {
      const k = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      if (k) { e.preventDefault(); select(tabs[(i + k + tabs.length) % tabs.length], true); }
      if (e.key === 'Home') { e.preventDefault(); select(tabs[0], true); }
      if (e.key === 'End') { e.preventDefault(); select(tabs[tabs.length - 1], true); }
    });
  });
  document.querySelectorAll('.bands').forEach((ul) => ul.querySelectorAll('li').forEach((li, i) => li.style.setProperty('--n', i)));

  // --- Quick bar: shows after the hero, takes the ground and ink of the chapter under it
  const bar = document.querySelector('.bar');
  const hero = document.querySelector('.hero');
  if (bar && hero && 'IntersectionObserver' in window) {
    new IntersectionObserver(([e]) => bar.classList.toggle('is-on', !e.isIntersecting), { threshold: 0.05 }).observe(hero);
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) {
        bar.style.setProperty('--header-bg', e.target.dataset.ground);
        bar.style.setProperty('--header-ink', e.target.dataset.ink);
      }
    }, { rootMargin: '0px 0px -94% 0px', threshold: 0 });
    document.querySelectorAll('[data-ground]').forEach((s) => io.observe(s));
  }
})();
