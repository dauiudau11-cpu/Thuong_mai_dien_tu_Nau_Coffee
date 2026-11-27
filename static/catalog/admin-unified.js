/* Shared Admin keyboard navigation; native Django filtering/CRUD is unchanged. */
document.addEventListener('DOMContentLoaded', () => {
  const button = document.querySelector('.nau-mobile-navigation');
  if (!button) return;
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && document.body.classList.contains('nau-nav-open')) {
      document.body.classList.remove('nau-nav-open');
      button.setAttribute('aria-expanded', 'false');
      button.focus();
    }
  });
});
