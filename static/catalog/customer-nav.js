(() => {
  const menu = document.querySelector('[data-customer-nav]');
  if (!menu) return;
  const summary = menu.querySelector('summary');
  const hover = window.matchMedia('(hover: hover) and (pointer: fine)');
  let closeTimer;
  const cancelClose = () => window.clearTimeout(closeTimer);
  menu.addEventListener('pointerenter', (event) => {
    if (!hover.matches || event.pointerType === 'touch') return;
    cancelClose();
    menu.open = true;
  });
  menu.addEventListener('pointerleave', () => {
    if (!hover.matches) return;
    closeTimer = window.setTimeout(() => {
      if (!menu.contains(document.activeElement)) menu.open = false;
    }, 180);
  });
  menu.addEventListener('focusin', cancelClose);
  menu.addEventListener('focusout', (event) => {
    if (!menu.contains(event.relatedTarget)) menu.open = false;
  });
  document.addEventListener('click', (event) => {
    if (!menu.contains(event.target)) menu.open = false;
  });
  menu.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      menu.open = false;
      summary.focus();
    }
  });
})();
