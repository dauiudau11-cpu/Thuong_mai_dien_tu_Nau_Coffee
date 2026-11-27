'use strict';
(() => {
  const form = document.querySelector('#password-reset-exchange');
  if (!form) return;
  const params = new URLSearchParams(location.hash.slice(1));
  const uid = params.get('uid'), token = params.get('token');
  if (location.hash) history.replaceState(null, '', location.pathname);
  if (!uid || !token || uid.length > 64 || token.length > 128) return;
  form.elements.uid.value = uid;
  form.elements.token.value = token;
  form.requestSubmit();
})();
