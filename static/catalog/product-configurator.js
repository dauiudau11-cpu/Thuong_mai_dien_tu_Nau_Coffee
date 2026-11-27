const drinkConfigurator = document.querySelector('.drink-configurator');
if (drinkConfigurator) {
  const picker = drinkConfigurator.querySelector('.drink-size-picker');
  const tabs = [...picker.querySelectorAll('[role=tab]')];
  const panels = [...drinkConfigurator.querySelectorAll('.drink-size-panel')];
  const selectSize = index => {
    tabs.forEach((tab, i) => {
      tab.setAttribute('aria-selected', String(i === index));
      tab.tabIndex = i === index ? 0 : -1;
      panels[i].hidden = i !== index;
      panels[i].setAttribute('role', 'tabpanel');
      panels[i].setAttribute('aria-labelledby', tab.id);
    });
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectSize(index));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      selectSize(next);
      tabs[next].focus();
    });
  });
  selectSize(0);
  picker.hidden = false;
}

document.querySelectorAll('[data-drink-preference]').forEach(group => {
  const custom = group.querySelector('.drink-preference-custom');
  const level = group.querySelector('.drink-preference-level');
  const output = group.querySelector('.drink-preference-value');
  const sync = () => {
    const mode = group.querySelector('input[type=radio]:checked');
    custom.hidden = mode.value !== 'custom';
    output.value = mode.value === 'custom' ? level.value : mode.dataset.option;
  };
  group.addEventListener('change', sync);
  sync();
});

document.querySelectorAll('.drink-quantity-stepper').forEach(stepper => {
  const input = stepper.querySelector('input[name=quantity]');
  const buttons = [...stepper.querySelectorAll('[data-quantity-step]')];
  const min = Number(input.min) || 1;
  const max = Number(input.max) || 99;
  const sync = () => {
    const value = input.valueAsNumber;
    buttons.forEach(button => {
      button.disabled = Number.isFinite(value) && (Number(button.dataset.quantityStep) < 0 ? value <= min : value >= max);
    });
  };
  buttons.forEach(button => {
    button.hidden = false;
    button.addEventListener('click', () => {
      const value = Number.isFinite(input.valueAsNumber) ? Math.trunc(input.valueAsNumber) : min;
      input.value = Math.min(max, Math.max(min, value + Number(button.dataset.quantityStep)));
      input.dispatchEvent(new Event('input', {bubbles:true}));
      input.dispatchEvent(new Event('change', {bubbles:true}));
    });
  });
  input.addEventListener('input', sync);
  sync();
});

// Store only drink preferences for the login round trip, never account inputs or CSRF.
if (drinkConfigurator) {
  const key = `nau-drink-draft:${location.pathname}`;
  const controls = [...drinkConfigurator.querySelectorAll('input, select')].filter(e => e.name && e.name !== 'csrfmiddlewaretoken');
  try {
    const raw = sessionStorage.getItem(key);
    sessionStorage.removeItem(key);
    const draft = raw ? JSON.parse(raw) : null;
    if (draft && Date.now() - draft.time < 30 * 60 * 1000 && Array.isArray(draft.fields)) {
      controls.forEach((input, index) => {
        const field = draft.fields[index];
        if (!field || field.name !== input.name || field.value?.length > 100) return;
        if (input.type === 'checkbox' || input.type === 'radio') input.checked = !!field.checked;
        else if (input.type !== 'hidden') input.value = field.value;
      });
      controls.forEach(input => { input.dispatchEvent(new Event('change', {bubbles:true})); input.dispatchEvent(new Event('input', {bubbles:true})); });
      const tab = [...drinkConfigurator.querySelectorAll('[role=tab]')].find(e => e.id === draft.tab);
      tab?.click();
    }
  } catch { /* An unavailable browser store must not block ordering. */ }
  drinkConfigurator.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => {
    try {
      if (drinkConfigurator.dataset.guest !== 'true') { sessionStorage.removeItem(key); return; }
      sessionStorage.setItem(key, JSON.stringify({time:Date.now(), tab:drinkConfigurator.querySelector('[aria-selected=true]')?.id,
        fields:controls.map(e => ({name:e.name, value:e.type === 'hidden' ? '' : e.value, checked:e.checked}))}));
    } catch { /* Continue normal authentication when storage is unavailable. */ }
  }));
}
