(() => {
  const app = document.querySelector('#staff-app');
  if (!app) return;
  const board = document.querySelector('#staff-board'), notice = document.querySelector('#staff-notice');
  const drawer = document.querySelector('#staff-drawer'), detail = document.querySelector('#staff-detail');
  let busy = false, fetching = false, opened = null, detailVersion = null;
  const failures = new Map();
  const csrf = document.querySelector('#staff-csrf input').value;
  async function json(url, options) {
    const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store', ...options});
    if (response.redirected || !(response.headers.get('content-type') || '').includes('application/json')) throw new Error('Phiên đăng nhập đã hết hoặc không đủ quyền. Hãy đăng nhập lại.');
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Không thể xử lý yêu cầu. Vui lòng thử lại.');
    return data;
  }
  async function openDetail(card) {
    opened = card.dataset.code;
    const code = opened;
    try {
      const data = await json(card.dataset.detail);
      if (opened !== code) return;
      detail.innerHTML = data.html; detailVersion = data.version;
      if (!drawer.open) drawer.showModal();
    } catch (error) { notice.textContent = error.message; }
  }
  async function refresh() {
    if (busy || fetching || document.hidden) return;
    fetching = true;
    try {
      const data = await json(app.dataset.feed);
      if (busy) return;
      // Only replace cards: drawer and unsaved note are deliberately outside this subtree.
      const previous = new Map(Array.from(board.querySelectorAll('[data-code]'), card => [card.dataset.code, card.dataset.version]));
      const scroll = {left: window.scrollX, top: window.scrollY};
      board.innerHTML = data.html;
      window.scrollTo(scroll);
      if (Array.from(board.querySelectorAll('[data-code]')).some(card => previous.has(card.dataset.code) && previous.get(card.dataset.code) !== card.dataset.version)) notice.textContent = 'Hàng chờ đã đồng bộ thay đổi mới. Hãy kiểm tra trạng thái trước khi xử lý.';
      failures.forEach((failure, code) => {
        const card = board.querySelector(`[data-code="${code}"]`);
        if (card && card.dataset.version === failure.version) card.querySelector('.staff-card-error').textContent = failure.message;
        else failures.delete(code);
      });
      if (opened && drawer.open) {
        const card = board.querySelector(`[data-code="${opened}"]`);
        if (card && card.dataset.version !== detailVersion) {
          notice.textContent = 'Đơn đang xem đã cập nhật. Chi tiết đã đồng bộ; ghi chú tạm được giữ.';
          await openDetail(card);
        }
      }
    } catch (error) { notice.textContent = error.message; }
    finally { fetching = false; }
  }
  app.addEventListener('click', async event => {
    const open = event.target.closest('[data-open]');
    if (open) { await openDetail(open.closest('[data-code]')); return; }
    const button = event.target.closest('[data-command]');
    if (!button || busy || fetching) return;
    const card = button.closest('[data-code]'), action = button.dataset.command;
    if (action === 'handover' && !window.confirm('Xác nhận đã bàn giao đúng đơn cho khách?')) return;
    if (action === 'cash' && !window.confirm('Xác nhận đã thu tiền theo nghiệp vụ mô phỏng?')) return;
    busy = true;
    card.querySelectorAll('button').forEach(b => b.disabled = true);
    const errorBox = card.querySelector('.staff-card-error'); errorBox.textContent = '';
    let failure = '';
    failures.delete(card.dataset.code);
    try {
      const data = await json(card.dataset.action, {method: 'POST', headers: {'X-CSRFToken': csrf},
        body: new URLSearchParams({action, version: card.dataset.version, confirmed: 'yes'})});
      notice.textContent = data.message;
    } catch (error) { failure = error.message; failures.set(card.dataset.code, {version: card.dataset.version, message: failure}); errorBox.textContent = failure; notice.textContent = failure; }
    finally {
      busy = false;
      card.querySelectorAll('button').forEach(b => b.disabled = false);
      await refresh();
      if (failure) {
        const current = board.querySelector(`[data-code="${card.dataset.code}"] .staff-card-error`);
        if (current) current.textContent = failure;
      }
    }
  });
  document.querySelector('#staff-close').addEventListener('click', () => drawer.close());
  drawer.addEventListener('close', () => { opened = null; detailVersion = null; });
  window.setInterval(refresh, 12000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
})();
