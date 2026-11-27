'use strict';
(() => {
  const input = document.querySelector('#customer-activation input[name="token"]');
  if (!input) return;
  const token = new URLSearchParams(location.hash.slice(1)).get('token');
  if (token && token.length <= 1024) input.value = token;
  if (location.hash) history.replaceState(null, '', location.pathname);
})();
