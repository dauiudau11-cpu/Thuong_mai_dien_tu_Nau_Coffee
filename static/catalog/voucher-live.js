/* Backend quotes are advisory; creating an order revalidates and redeems atomically. */
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form[data-voucher-quote]');
  if (!form) return;
  const select = form.querySelector('[name=voucher]');
  const status = form.querySelector('[data-voucher-status]');
  const buttons = [...form.querySelectorAll('button:not([type=button])')];
  let timer, controller, sequence = 0, quotedInput = null, lastQuote = null;
  const inputSignature = () => JSON.stringify([...new FormData(form).entries()]);
  const money = value => new Intl.NumberFormat('vi-VN').format(value) + ' đ';
  const renderTotals = data => {
    document.querySelectorAll('[data-voucher-discount]').forEach(node => node.textContent = money(data.discount));
    document.querySelectorAll('[data-voucher-total]').forEach(node => node.textContent = money(data.total));
    const subtotal = document.getElementById('manual-subtotal');
    if (subtotal) subtotal.textContent = money(data.subtotal);
  };
  async function refresh() {
    const current = ++sequence;
    if (controller) controller.abort();
    controller = new AbortController();
    const app = form.querySelector('[name=channel]')?.value === 'APP';
    select.disabled = app;
    if (app) select.value = '';
    quotedInput = inputSignature();
    buttons.forEach(button => button.disabled = true);
    status.textContent = 'Đang cập nhật tổng tiền…';
    try {
      const response = await fetch(form.dataset.voucherQuote, {method:'POST', body:new FormData(form),
        headers:{'X-CSRFToken':form.querySelector('[name=csrfmiddlewaretoken]').value}, signal:controller.signal});
      const data = await response.json();
      if (current !== sequence) return;
      if (!response.ok) throw new Error(data.error || 'Không thể cập nhật giá.');
      const chosen = select.value;
      select.replaceChildren(new Option('Không dùng voucher', ''), ...data.choices.map(item => new Option(item.label, String(item.id))));
      select.value = chosen;
      lastQuote = {signature: quotedInput, data};
      renderTotals(data);
      status.textContent = app ? 'Đơn APP không áp dụng voucher.' : 'Ưu đãi đã được áp dụng.';
      buttons.forEach(button => button.disabled = false);
    } catch (error) {
      if (error.name === 'AbortError' || current !== sequence) return;
      status.textContent = error.message;
      document.querySelectorAll('[data-voucher-total]').forEach(node => node.textContent = 'Chưa xác nhận');
    }
  }
  const schedule = () => {
    // Blur may emit change after input already produced the same successful quote.
    // Keep the submit click enabled when no quote input has actually changed.
    const signature = inputSignature();
    if (signature === quotedInput) {
      // The existing POS listener may have rendered its local subtotal on blur.
      // Restore the backend quote only for these exact, unchanged inputs.
      if (lastQuote?.signature === signature) renderTotals(lastQuote.data);
      return;
    }
    quotedInput = signature;
    clearTimeout(timer); ++sequence; controller?.abort(); buttons.forEach(button => button.disabled = true); timer = setTimeout(refresh, 250); };
  form.addEventListener('input', schedule);
  form.addEventListener('change', schedule);
  form.addEventListener('click', event => { if (event.target.closest('[type=button]')) setTimeout(schedule,0); });
  refresh();
});
