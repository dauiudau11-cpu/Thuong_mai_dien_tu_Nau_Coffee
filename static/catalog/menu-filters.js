const menuFilters = document.querySelector('.menu-filter-disclosure');
if (menuFilters) {
  const desktopFilters = window.matchMedia('(min-width: 768px)');
  const syncMenuFilters = () => { menuFilters.open = desktopFilters.matches; };
  desktopFilters.addEventListener('change', syncMenuFilters);
  syncMenuFilters();
  const form = menuFilters.querySelector('form');
  const results = document.querySelector('.menu-results');
  const status = document.querySelector('.menu-filter-status');
  let controller;
  let requestId = 0;
  let searchTimer;
  const search = form.querySelector('input[name=q]');
  const clearSearch = form.querySelector('.menu-search-clear');
  const syncClearSearch = () => { clearSearch.hidden = !search.value; };
  const formURL = () => {
    const url = new URL(form.action);
    for (const [key, value] of new FormData(form)) if (value) url.searchParams.set(key, value);
    return url;
  };
  const syncChoices = () => {
    const params = new URL(location.href).searchParams;
    const sort = form.querySelector('select[name=sort]');
    sort.value = params.get('sort') || '';
    search.value = params.get('q') || '';
    syncClearSearch();
    if (sort.selectedIndex < 0) sort.value = '';
    form.querySelectorAll('input[type=checkbox]').forEach(input => {
      input.checked = params.get(input.name) === input.value;
    });
  };
  const updateResults = async (url, pushHistory = true) => {
    controller?.abort();
    controller = new AbortController();
    const id = ++requestId;
    results.setAttribute('aria-busy', 'true');
    status.classList.add('sr-only');
    status.textContent = 'Đang cập nhật thực đơn…';
    try {
      const response = await fetch(url, {signal: controller.signal, headers: {'X-Requested-With': 'XMLHttpRequest'}});
      if (!response.ok) throw new Error('Menu request failed');
      const documentResult = new DOMParser().parseFromString(await response.text(), 'text/html');
      const nextResults = documentResult.querySelector('.menu-results');
      if (!nextResults) throw new Error('Menu results missing');
      if (id !== requestId) return;
      results.replaceChildren(...nextResults.childNodes);
      if (pushHistory && url.href !== location.href) history.pushState({}, '', url);
      status.textContent = results.querySelector('.section-heading p')?.textContent || 'Đã cập nhật thực đơn.';
    } catch (error) {
      if (error.name === 'AbortError' || id !== requestId) return;
      syncChoices();
      status.classList.remove('sr-only');
      status.textContent = 'Chưa cập nhật được thực đơn. Bạn vui lòng chọn lại.';
    } finally {
      if (id === requestId) results.removeAttribute('aria-busy');
    }
  };
  form.addEventListener('submit', event => {
    event.preventDefault();
    clearTimeout(searchTimer);
    updateResults(formURL());
  });
  search.addEventListener('input', () => {
    syncClearSearch();
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => updateResults(formURL()), 300);
  });
  clearSearch.addEventListener('click', () => {
    clearTimeout(searchTimer);
    search.value = '';
    syncClearSearch();
    search.focus();
    updateResults(formURL());
  });
  form.addEventListener('change', event => {
    const input = event.target;
    if (!input.matches('input[type=checkbox], select[name=sort]')) return;
    if (input.checked) form.querySelectorAll(`input[name="${input.name}"]`).forEach(other => {
      if (other !== input) other.checked = false;
    });
    updateResults(formURL());
  });
  results.addEventListener('click', event => {
    const clear = event.target.closest('[data-clear-search]');
    if (clear) {
      event.preventDefault();
      search.value = '';
      syncClearSearch();
      updateResults(new URL(clear.href));
      return;
    }
    const link = event.target.closest('.pagination a');
    if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    updateResults(new URL(link.href));
  });
  window.addEventListener('popstate', () => { syncChoices(); updateResults(new URL(location.href), false); });
}
