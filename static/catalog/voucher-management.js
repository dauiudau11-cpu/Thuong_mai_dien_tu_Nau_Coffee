document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.voucher-editor');
  if (!form) return;
  const audience = form.querySelector('[name="audience"]');
  const section = form.querySelector('[data-private-section]');
  const results = form.querySelector('[data-customer-results]');
  const rows = form.querySelector('[data-allocation-rows]');
  const total = form.querySelector('[name="alloc-TOTAL_FORMS"]');
  const update = () => {
    const isPrivate = audience.value === 'PRIVATE';
    section.hidden = !isPrivate;
    if (form.dataset.readOnly === 'true') return;
    rows.querySelectorAll('input').forEach(input => {
      if (!input.name.endsWith('-label')) input.disabled = !isPrivate;
    });
    total.value = isPrivate ? String(rows.children.length) : '0';
    if (!isPrivate) form.querySelector('[name="alloc-INITIAL_FORMS"]').value='0';
  };
  audience.addEventListener('change', update); update();
  form.querySelector('[data-search-customer]')?.addEventListener('click', async () => {
    results.replaceChildren();
    try {
      const response = await fetch(form.dataset.customerSearch, {method:'POST', credentials:'same-origin', headers:{'X-CSRFToken':form.querySelector('[name=csrfmiddlewaretoken]').value}, body:new URLSearchParams({q:form.querySelector('#voucher-customer-query').value,voucher_id:form.dataset.voucherId})});
      if (!response.ok) throw new Error();
      const data = await response.json();
      if (!data.customers.length) results.textContent = 'Không tìm thấy khách hàng đã xác minh phù hợp.';
      data.customers.forEach(customer => {
        const button = document.createElement('button'); button.type='button'; button.textContent=customer.label;
        button.addEventListener('click', () => {
          const existing = rows.querySelector(`[data-customer-id="${customer.id}"]`);
          if (existing) {existing.querySelector('input[type=checkbox]').checked=true;existing.querySelector('input[type=number]').focus();return;}
          const index=Number(total.value);
          if (index>=100) {results.textContent='Đã đạt 100 khách trong một lần lưu.';return;}
          const tr=document.createElement('tr');tr.dataset.customerId=String(customer.id);
          const selected=document.createElement('td');const label=document.createElement('td');const quota=document.createElement('td');
          const field=(type,name,value)=>{const input=document.createElement('input');input.type=type;input.name=`alloc-${index}-${name}`;input.value=value;return input;};
          const checkbox=field('checkbox','selected','on');checkbox.checked=true;checkbox.setAttribute('aria-label',`Áp dụng cho ${customer.label}`);selected.append(checkbox,field('hidden','customer_id',customer.id),field('hidden','expected',String(customer.allocated || 0)));
          label.textContent=customer.label;
          const amount=field('number','allocated',String(customer.has_grant ? customer.allocated : 1));amount.min='0';amount.max='2147483647';amount.required=true;amount.setAttribute('aria-label',`Tổng lượt cấp cho ${customer.label}`);quota.append(amount);
          tr.append(selected,label,quota);rows.append(tr);total.value=String(index+1);amount.focus();
        });results.append(button);
      });
    } catch {results.textContent='Không tải được danh sách khách. Vui lòng thử lại.';}
  });
  form.querySelector('[data-clear-unselected]')?.addEventListener('click', () => {
    rows.querySelectorAll('tr').forEach(row => {if (!row.querySelector('input[type=checkbox]').checked) row.remove();});
    rows.querySelectorAll('tr').forEach((row,index) => {row.querySelectorAll('[name]').forEach(input => {input.name=input.name.replace(/alloc-\d+-/, `alloc-${index}-`);});});
    total.value=String(rows.children.length);
    form.querySelector('[name="alloc-INITIAL_FORMS"]').value='0';
  });
  let submitting=false;
  form.addEventListener('submit', event=>{if (submitting) event.preventDefault();else if(form.checkValidity()) submitting=true;});
});
