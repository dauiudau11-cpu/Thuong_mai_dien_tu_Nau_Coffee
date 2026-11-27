// Progressive enhancement only: server validation and prices remain authoritative.
document.querySelectorAll('.map-embed').forEach((details) => {
  details.addEventListener('toggle', () => {
    const frame = details.querySelector('iframe[data-map-src]');
    if (details.open && frame && !frame.hasAttribute('src')) {
      frame.src = frame.dataset.mapSrc;
    }
  });
});

document.querySelectorAll('[data-review-loop] .premium-voice-track').forEach((track) => {
  const cards = [...track.children];
  if (cards.length > 1) cards.forEach((card) => track.append(card.cloneNode(true)));
});

const channel = document.querySelector('.manual-order-form #id_channel');
const reference = document.querySelector('.manual-order-form #id_external_reference');
const help = document.querySelector('#channel-help');
if (channel && reference && help) {
  reference.setAttribute('aria-describedby', 'channel-help');
  const updateChannel = () => {
    reference.required = channel.value === 'APP';
    help.textContent = channel.value === 'APP'
      ? 'APP: mã tham chiếu là bắt buộc; giá APP được máy chủ tính lại. Chưa ghi nhận thu tiền / đối soát.'
      : 'COUNTER: giá tại quầy được máy chủ tính lại. Mã tham chiếu không bắt buộc; chưa ghi nhận thu tiền.';
  };
  channel.addEventListener('change', updateChannel);
  updateChannel();
}

document.querySelectorAll('header nav a').forEach((link) => {
  if (new URL(link.href).pathname === window.location.pathname) {
    link.setAttribute('aria-current', 'page');
  }
});

// Keep keyboard navigation and mobile disclosure usable without a UI framework.
document.querySelectorAll('.account-tabs a, .operations-sidebar a').forEach((link) => {
  if (new URL(link.href).pathname === window.location.pathname) {
    link.setAttribute('aria-current', 'page');
  }
});
document.querySelectorAll('.mobile-menu').forEach((menu) => {
  menu.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu.open) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
});

// A preview from server-rendered prices only. The server still validates/reprices POST.
document.querySelectorAll('.purchase-form').forEach((form) => {
  const quantity = form.querySelector('[name="quantity"]');
  const output = form.querySelector('output');
  const options = [...form.querySelectorAll('[name="options"]')];
  const update = (event) => {
    const changed = event?.target;
    if (changed?.checked && ['SUGAR', 'ICE'].includes(changed.dataset.kind)) {
      options.filter((option) => option !== changed && option.dataset.kind === changed.dataset.kind)
        .forEach((option) => { option.checked = false; });
    }
    const count = Number(quantity.value);
    const unit = Number(form.dataset.unitPrice) + options.filter((option) => option.checked)
      .reduce((sum, option) => sum + Number(option.dataset.price), 0);
    const total = unit * count;
    output.textContent = Number.isSafeInteger(total) && total >= 0 && count >= 1 && count <= 99
      ? new Intl.NumberFormat('vi-VN').format(total) + ' đ' : 'Kiểm tra số lượng';
  };
  form.addEventListener('input', update);
  update();
});

const purchaseBar = document.querySelector('.mobile-purchase-bar');
if (purchaseBar && 'IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    purchaseBar.hidden = entries.some((entry) => entry.isIntersecting);
  });
  document.querySelectorAll('.purchase-controls').forEach((controls) => observer.observe(controls));
}

const manualForm = document.querySelector('.manual-order-form');
const catalogData = document.querySelector('#manual-catalog');
if (manualForm && catalogData) {
  const catalog = JSON.parse(catalogData.textContent);
  const container = manualForm.querySelector('.manual-lines');
  const template = manualForm.querySelector('#manual-empty-form');
  const total = manualForm.querySelector('#id_lines-TOTAL_FORMS');
  const maximum = Number(manualForm.querySelector('#id_lines-MAX_NUM_FORMS').value);
  const add = manualForm.querySelector('#add-manual-line');
  const status = manualForm.querySelector('#manual-line-status');
  const money = (amount) => new Intl.NumberFormat('vi-VN').format(amount) + ' đ';
  const update = () => {
    const rows = [...container.querySelectorAll('.manual-line')];
    let subtotal = 0, invalid = 0;
    rows.forEach((row, index) => {
      row.querySelector('legend').textContent = `Món ${index + 1}`;
      row.querySelectorAll('[name], [id], [for], [aria-describedby]').forEach((element) => {
        ['name', 'id', 'for', 'aria-describedby'].forEach((attribute) => {
          if (element.hasAttribute(attribute)) {
            element.setAttribute(attribute, element.getAttribute(attribute).replace(/lines-(\d+|__prefix__)-/g, `lines-${index}-`));
          }
        });
      });
      const remove = row.querySelector('.remove-line');
      remove.hidden = false;
      remove.disabled = rows.length === 1;
      const variant = catalog.variants.find((entry) => String(entry.id) === row.querySelector('[name$="-variant"]').value);
      const options = row.querySelector('[name$="-options"]');
      [...(options?.options || [])].forEach((option) => {
        const entry = catalog.options.find((item) => String(item.id) === option.value);
        option.hidden = !variant || entry?.product_id !== variant.product_id;
        option.disabled = option.hidden;
        if (option.hidden) option.selected = false;
      });
      if (options?.closest('p')) options.closest('p').hidden = !variant || ![...options.options].some((option) => !option.disabled);
      const base = variant?.prices[channel.value];
      const count = Number(row.querySelector('[name$="-quantity"]').value);
      const extra = [...(options?.selectedOptions || [])].reduce((sum, option) => sum +
        catalog.options.find((item) => String(item.id) === option.value).price_delta, 0);
      const deleted = row.querySelector('[name$="-DELETE"]')?.checked;
      const valid = base !== undefined && Number.isInteger(count) && count >= 1 && count <= 99;
      if (!deleted && valid) subtotal += (base + extra) * count;
      else if (!deleted && (variant || row.querySelector('[name$="-quantity"]').value)) invalid++;
      row.querySelector('.manual-line-total').textContent = deleted ? 'Dòng đã đánh dấu bỏ' : valid
        ? `${channel.value} · Đơn giá ${money(base + extra)} · Tạm tính ${money((base + extra) * count)}`
        : 'Chọn món và số lượng hợp lệ để xem tạm tính';
    });
    document.querySelectorAll('.pos-select').forEach((card) => {
      const entry = catalog.variants.find((item) => String(item.id) === card.dataset.variant);
      const price = entry?.prices[channel.value];
      card.disabled = price === undefined;
      card.querySelector('.pos-price').textContent = price === undefined ? 'Chưa có giá kênh này' : money(price);
    });
    total.value = rows.length;
    const summary = manualForm.querySelector('#manual-subtotal');
    if (summary) summary.textContent = money(subtotal);
    const grand = manualForm.querySelector('#manual-grand-total');
    if (grand) grand.textContent = invalid ? `Cần kiểm tra ${invalid} dòng món` : money(subtotal);
    add.disabled = rows.length >= maximum;
    status.textContent = `${rows.length}/${maximum} dòng món · Giá cuối được máy chủ xác nhận.`;
  };
  // Preserve every bound form/error on failed POST; initial JS view starts with one line.
  if (manualForm.dataset.bound !== 'true') {
    [...container.querySelectorAll('.manual-line')].slice(1).forEach((row) => row.remove());
  }
  add.hidden = false;
  add.addEventListener('click', () => {
    if (container.children.length >= maximum) return;
    container.append(template.content.cloneNode(true));
    update();
    container.lastElementChild.querySelector('select').focus();
  });
  container.addEventListener('click', (event) => {
    if (!event.target.closest('.remove-line')) return;
    if (container.children.length > 1) {
      event.target.closest('.manual-line').remove();
      update();
      add.focus();
    }
  });
  manualForm.addEventListener('input', update);
  manualForm.addEventListener('change', update);
  document.querySelectorAll('.pos-select').forEach((card) => {
    card.hidden = false;
    card.addEventListener('click', () => {
      let row = [...container.querySelectorAll('.manual-line')].find((item) => !item.querySelector('[name$="-variant"]').value);
      if (!row) {
        if (container.children.length >= maximum) {
          status.textContent = 'Đã đạt số dòng tối đa. Hãy sửa số lượng ở dòng món đã chọn.';
          return;
        }
        add.click();
        row = container.lastElementChild;
      }
      row.querySelector('[name$="-variant"]').value = card.dataset.variant;
      row.querySelector('[name$="-quantity"]').value = '1';
      update();
      row.scrollIntoView({block: 'nearest'});
      row.querySelector('[name$="-quantity"]').focus();
    });
  });
  update();
}

// Server-side permissions and payment state remain authoritative.
document.querySelectorAll('form[data-confirm-refund]').forEach(form => {
  form.addEventListener('submit', event => {
    if (!window.confirm('Xác nhận hoàn toàn bộ số tiền mô phỏng cho đúng đơn này? Không phát sinh tiền thật.')) event.preventDefault();
  });
});
