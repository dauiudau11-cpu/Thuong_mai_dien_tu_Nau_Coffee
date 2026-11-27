(() => {
  const page = document.querySelector('.basket-page');
  if (!page) return;
  const status = page.querySelector('[data-cart-status]');
  const recovery = page.querySelector('[data-cart-recovery]');
  const checkout = page.querySelector('a[href][class*="basket-checkout"]');
  const checkoutURL = checkout?.getAttribute('href');
  const states = [];
  const money = (value) => new Intl.NumberFormat('vi-VN').format(Number(value)) + ' đ';
  let timer = null;
  let sending = false;
  const valid = (state) => Number.isInteger(state.input.valueAsNumber) && state.input.valueAsNumber >= 1 && state.input.valueAsNumber <= 99;
  const dirty = (state) => valid(state) && state.input.valueAsNumber !== state.saved;
  const sync = () => {
    const busy = sending || timer !== null || states.some((state) => !valid(state) || dirty(state) || state.failed);
    page.querySelector('.basket-layout')?.setAttribute('aria-busy', String(busy));
    if (checkout) {
      checkout.setAttribute('aria-disabled', String(busy));
      if (busy) checkout.removeAttribute('href');
      else checkout.setAttribute('href', checkoutURL);
    }
    states.forEach((state) => state.buttons.forEach((button) => {
      button.disabled = Number(button.dataset.cartStep) < 0 ? state.input.valueAsNumber <= 1 : state.input.valueAsNumber >= 99;
    }));
  };
  const apply = (data) => {
    data.rows.forEach((row) => {
      const state = states.find((entry) => entry.id === row.id);
      if (!state) return;
      const total = state.card.querySelector('.basket-line-total strong');
      const unit = state.card.querySelector('.basket-line-total small');
      if (total) total.textContent = money(row.total);
      if (unit) unit.textContent = money(row.unit) + ' / ly';
    });
    const fields = {'[data-cart-total]': money(data.total), '[data-cart-subtotal]': money(data.subtotal), '[data-cart-discount]': '−' + money(data.discount), '[data-cart-quantity]': data.quantity + ' món'};
    Object.entries(fields).forEach(([selector, value]) => {
      const field = page.querySelector(selector);
      if (field) field.textContent = value;
    });
    const badge = document.querySelector('.cart-quantity-badge');
    if (badge) {
      badge.textContent = data.quantity > 99 ? '99+' : String(data.quantity);
      badge.closest('a').setAttribute('aria-label', 'Giỏ hàng, ' + data.quantity + ' sản phẩm');
    }
  };
  const drain = async () => {
    if (sending) return;
    sending = true;
    sync();
    try {
      // One write at a time across the cart. New clicks are coalesced into the next write.
      let state;
      while ((state = states.find((entry) => !entry.failed && dirty(entry)))) {
        const quantity = state.input.valueAsNumber;
        const revision = state.revision;
        const body = new FormData(state.form);
        body.set('quantity', String(quantity));
        status.textContent = 'Đang cập nhật giỏ hàng…';
        try {
          const response = await fetch(state.form.action, {method: 'POST', body, credentials: 'same-origin', headers: {'Accept': 'application/json'}});
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || 'Không thể cập nhật giỏ hàng.');
          if (!Array.isArray(data.rows) || !data.rows.some((row) => row.id === state.id && row.quantity === quantity)) throw new Error('Không thể xác nhận số lượng đã lưu.');
          state.saved = quantity;
          apply(data);
          status.textContent = 'Đã cập nhật giỏ hàng.';
          recovery.hidden = true;
        } catch (error) {
          state.failed = true;
          status.textContent = error instanceof TypeError || error instanceof SyntaxError ? 'Kết nối bị gián đoạn. Vui lòng tải lại để kiểm tra giỏ hàng.' : error.message;
          recovery.hidden = false;
          // Never overwrite a newer edit with the response to an older request.
          if (revision !== state.revision) state.failed = false;
        }
      }
    } finally {
      sending = false;
      if (states.some((state) => !valid(state))) {
        status.textContent = 'Số lượng phải là số nguyên từ 1 đến 99.';
      } else if (timer === null && states.every((state) => !dirty(state) && !state.failed)) {
        status.textContent = 'Đã cập nhật giỏ hàng.';
        recovery.hidden = true;
      }
      sync();
    }
  };
  const schedule = (state, immediate = false) => {
    state.revision += 1;
    state.failed = false;
    clearTimeout(timer);
    timer = null;
    if (!valid(state)) {
      status.textContent = 'Số lượng phải là số nguyên từ 1 đến 99.';
      sync();
      return;
    }
    status.textContent = 'Đang cập nhật giỏ hàng…';
    if (immediate) drain();
    else timer = setTimeout(() => {timer = null; drain();}, 200);
    sync();
  };
  page.querySelectorAll('[data-cart-stepper]').forEach((stepper) => {
    const input = stepper.querySelector('input');
    const form = stepper.closest('form');
    const card = form.closest('[data-cart-item]');
    const buttons = [...stepper.querySelectorAll('[data-cart-step]')];
    const state = {input, form, card, buttons, id: Number(card.dataset.cartItem), saved: input.valueAsNumber, revision: 0, failed: false};
    states.push(state);
    buttons.forEach((button) => {
      button.hidden = false;
      button.addEventListener('click', () => {
        const current = input.valueAsNumber;
        input.value = String(Math.min(99, Math.max(1, (Number.isFinite(current) ? current : 1) + Number(button.dataset.cartStep))));
        input.dispatchEvent(new Event('input', {bubbles: true}));
      });
    });
    input.addEventListener('input', () => schedule(state));
    input.addEventListener('change', () => schedule(state, true));
    form.addEventListener('submit', (event) => {event.preventDefault(); schedule(state, true);});
  });
  checkout?.addEventListener('click', (event) => {
    if (checkout.getAttribute('aria-disabled') === 'true') event.preventDefault();
  });
  page.querySelectorAll('.basket-remove').forEach((form) => form.addEventListener('submit', (event) => {
    if (sending || timer !== null || states.some((state) => !valid(state) || dirty(state) || state.failed)) {
      event.preventDefault();
      status.textContent = 'Vui lòng chờ cập nhật giỏ hàng xong trước khi xóa món.';
    }
  }));
  sync();
})();
