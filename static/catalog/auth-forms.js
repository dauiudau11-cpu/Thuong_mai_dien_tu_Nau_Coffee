document.querySelectorAll('.auth-layout .auth input[type=password]').forEach(input => {
  const wrapper = document.createElement('div');
  wrapper.className = 'password-control';
  input.before(wrapper);
  wrapper.append(input);
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'password-toggle';
  const eye = '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>';
  const eyeOff = '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m3 3 18 18M10.6 5.1 12 5c6.5 0 10 7 10 7a18 18 0 0 1-3.1 4M6.5 6.5A20 20 0 0 0 2 12s3.5 7 10 7a12 12 0 0 0 5.5-1.5M10 10a3 3 0 0 0 4 4"/></svg>';
  button.innerHTML = eye;
  button.setAttribute('aria-label', `Hiện mật khẩu: ${input.labels?.[0]?.textContent || 'Mật khẩu'}`);
  button.setAttribute('aria-pressed', 'false');
  button.addEventListener('click', () => {
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.innerHTML = show ? eyeOff : eye;
    button.setAttribute('aria-pressed', String(show));
    button.setAttribute('aria-label', `${show ? 'Ẩn' : 'Hiện'} mật khẩu: ${input.labels?.[0]?.textContent || 'Mật khẩu'}`);
  });
  wrapper.append(button);
});
