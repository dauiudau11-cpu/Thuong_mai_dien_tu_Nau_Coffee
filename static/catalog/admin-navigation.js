/* Local navigation state only; native Django sidebar and CRUD stay intact. */
(() => {
  const PREFIX = 'nau.admin.navigation.';
  const SIDEBAR_KEY = `${PREFIX}sidebar`;
  const pageKey = url => `${PREFIX}page:${url.pathname}${url.search}`;
  const storage = {
    get(key) {
      try { return sessionStorage.getItem(key); } catch (_error) { return null; }
    },
    set(key, value) {
      try { sessionStorage.setItem(key, String(value)); } catch (_error) { /* Progressive fallback. */ }
    },
  };

  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

  document.addEventListener('DOMContentLoaded', () => {
  const button = document.querySelector('.nau-mobile-navigation');
  const sidebar = document.getElementById('nav-sidebar');
  if (!button || !sidebar) { if (button) button.hidden = true; return; }
  const currentPageKey = pageKey(new URL(location.href));
  let navigating = false;
  let lastKnownScroll = scrollY;
  let restoringMain = true;

  const savedSidebar = Number(storage.get(SIDEBAR_KEY));
  if (Number.isFinite(savedSidebar) && savedSidebar >= 0) sidebar.scrollTop = savedSidebar;
  requestAnimationFrame(() => {
    if (Number.isFinite(savedSidebar) && savedSidebar >= 0) sidebar.scrollTop = savedSidebar;
  });
  sidebar.addEventListener('scroll', () => storage.set(SIDEBAR_KEY, sidebar.scrollTop), {passive: true});

  button.addEventListener('click', () => {
    const expanded = button.getAttribute('aria-expanded') !== 'true';
    button.setAttribute('aria-expanded', String(expanded));
    document.body.classList.toggle('nau-nav-open', expanded);
  });

  const hasFormErrors = document.querySelector('.errornote, .errorlist, [aria-invalid="true"]');
  const restoreMainScroll = () => {
    if (hasFormErrors || location.hash) { restoringMain = false; return; }
    const stored = storage.get(currentPageKey);
    if (stored === null) { restoringMain = false; return; }
    const saved = Number(stored);
    if (!Number.isFinite(saved) || saved < 0) { restoringMain = false; return; }
    restoringMain = true;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const target = Math.min(saved, Math.max(0, document.documentElement.scrollHeight - innerHeight));
      lastKnownScroll = target;
      storage.set(currentPageKey, target);
      window.scrollTo({top: target, behavior: 'auto'});
      requestAnimationFrame(() => { restoringMain = false; });
    }));
  };

  document.addEventListener('pointerdown', event => {
    const link = event.target.closest('a[href]');
    if (!link || event.button !== 0 || link.target || link.hasAttribute('download')) return;
    const destination = new URL(link.href, location.href);
    if (destination.origin !== location.origin) return;
    lastKnownScroll = scrollY;
    storage.set(SIDEBAR_KEY, sidebar.scrollTop);
    storage.set(currentPageKey, lastKnownScroll);
    if (link.closest('#nav-sidebar, .reference-tabs')) storage.set(pageKey(destination), lastKnownScroll);
  }, true);

  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey
        || event.shiftKey || event.altKey || link.target || link.hasAttribute('download')) return;
    const destination = new URL(link.href, location.href);
    if (destination.origin !== location.origin) return;
    const remembered = Number(storage.get(currentPageKey));
    if (Number.isFinite(remembered) && remembered >= 0) lastKnownScroll = remembered;
    storage.set(SIDEBAR_KEY, sidebar.scrollTop);
    storage.set(currentPageKey, lastKnownScroll);
    if (link.closest('#nav-sidebar, .reference-tabs')) storage.set(pageKey(destination), lastKnownScroll);
    navigating = true;
  });

  window.addEventListener('scroll', () => {
    if (navigating || restoringMain) return;
    lastKnownScroll = scrollY;
    storage.set(currentPageKey, lastKnownScroll);
  }, {passive: true});
  const saveCurrentPosition = () => {
    storage.set(SIDEBAR_KEY, sidebar.scrollTop);
    storage.set(currentPageKey, lastKnownScroll);
  };
  window.addEventListener('pagehide', saveCurrentPosition);
  window.addEventListener('pageshow', event => { if (event.persisted) restoreMainScroll(); });
  restoreMainScroll();
  });
})();
