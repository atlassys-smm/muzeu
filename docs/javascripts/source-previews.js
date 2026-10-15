// Inline source excerpts are prepared at build time. No requests or dependencies.
(() => {
  const popup = document.createElement('div');
  popup.id = 'source-preview';
  popup.className = 'source-preview';
  popup.setAttribute('role', 'tooltip');
  popup.hidden = true;
  document.body.append(popup);
  let active, timer;
  const close = () => {
    clearTimeout(timer);
    if (active) active.removeAttribute('aria-describedby');
    active = null;
    popup.hidden = true;
  };
  const deferClose = () => { clearTimeout(timer); timer = setTimeout(close, 220); };
  const show = link => {
    clearTimeout(timer);
    if (active && active !== link) active.removeAttribute('aria-describedby');
    active = link;
    const heading = document.createElement('strong');
    heading.textContent = link.dataset.sourceTitle;
    const excerpt = document.createElement('p');
    excerpt.textContent = link.dataset.sourceExcerpt || 'Открыть исходный раздел документа.';
    const open = document.createElement('a');
    open.textContent = 'Открыть источник в новой вкладке ↗';
    open.href = link.href;
    open.target = '_blank';
    open.rel = 'noopener noreferrer';
    popup.replaceChildren(heading, excerpt, open);
    popup.hidden = false;
    link.setAttribute('aria-describedby', popup.id);
    const box = link.getBoundingClientRect();
    const left = Math.max(12, Math.min(box.left, innerWidth - popup.offsetWidth - 12));
    let top = box.bottom + 8;
    if (top + popup.offsetHeight > innerHeight - 12) top = Math.max(12, box.top - popup.offsetHeight - 8);
    popup.style.left = `${left}px`;
    popup.style.top = `${top}px`;
  };
  document.querySelectorAll('a.source-reference').forEach(link => {
    link.addEventListener('pointerenter', e => {
      if (e.pointerType === 'touch') return;
      clearTimeout(timer);
      timer = setTimeout(() => show(link), 180);
    });
    link.addEventListener('pointerleave', deferClose);
    link.addEventListener('focus', () => show(link));
    link.addEventListener('blur', deferClose);
  });
  popup.addEventListener('pointerenter', () => clearTimeout(timer));
  popup.addEventListener('pointerleave', deferClose);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  document.addEventListener('pointerdown', e => {
    if (!popup.contains(e.target) && !e.target.closest('a.source-reference')) close();
  });
  window.addEventListener('scroll', close, { passive: true });
  window.addEventListener('resize', close);
})();
