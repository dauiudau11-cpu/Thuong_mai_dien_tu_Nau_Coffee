/* Progressive enhancement; native SVG titles still work without JavaScript. */
document.addEventListener('DOMContentLoaded', () => {
  const dashboard = document.querySelector('.traffic-dashboard');
  const tip = dashboard?.querySelector('.traffic-tooltip');
  if (!tip) return;
  dashboard.querySelectorAll('[data-tooltip]').forEach(bar => {
    const show = () => {
      tip.textContent = bar.dataset.tooltip;
      tip.hidden = false;
      const box = bar.getBoundingClientRect();
      tip.style.left = `${Math.max(8, Math.min(box.left, innerWidth - tip.offsetWidth - 8))}px`;
      tip.style.top = `${Math.max(8, box.top - tip.offsetHeight - 10)}px`;
    };
    const hide = () => { tip.hidden = true; };
    bar.addEventListener('pointerenter', show);
    bar.addEventListener('pointerleave', hide);
    bar.addEventListener('focus', show);
    bar.addEventListener('blur', hide);
    bar.addEventListener('keydown', event => { if (event.key === 'Escape') hide(); });
  });
  document.addEventListener('scroll', () => { tip.hidden = true; }, true);
});
