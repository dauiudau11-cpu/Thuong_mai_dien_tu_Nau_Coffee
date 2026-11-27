const reviewCarousel = document.querySelector('.home-review-carousel');

if (reviewCarousel) {
  const viewport = reviewCarousel.querySelector('.home-review-viewport');
  const track = reviewCarousel.querySelector('.premium-voice-grid');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let animation;
  let heldPointer = null;
  let keyboardHeld = false;
  const cards = Array.from(track.children);
  const copies = cards.map(card => {
    const copy = card.cloneNode(true);
    copy.setAttribute('aria-hidden', 'true');
    return copy;
  });

  const updateLayout = () => {
    const canSlide = cards.length > 0 && !reducedMotion.matches;
    viewport.classList.toggle('is-sliding', canSlide);
    if (!canSlide) {
      animation?.cancel();
      animation = undefined;
      copies.forEach(copy => copy.remove());
      return;
    }

    if (!copies[0].parentNode) track.append(...copies);
    viewport.scrollLeft = 0;
    const distance = copies[0].getBoundingClientRect().left - cards[0].getBoundingClientRect().left;
    if (distance <= 0) return;
    const progress = animation?.effect.getComputedTiming().progress ?? 0;
    animation?.cancel();
    const duration = distance / (reducedMotion.matches ? 20 : 45) * 1000;
    animation = track.animate([
      {transform: 'translateX(0)'},
      {transform: `translateX(-${distance}px)`},
    ], {duration, iterations: Infinity, easing: 'linear'});
    animation.currentTime = progress * duration;
    updatePlayback();
  };

  const updatePlayback = () => {
    if (heldPointer !== null || keyboardHeld) animation?.pause();
    else animation?.play();
  };

  viewport.addEventListener('pointerdown', event => {
    if (!animation || !event.isPrimary || event.button !== 0 || !event.target.closest('article')) return;
    viewport.setPointerCapture(event.pointerId);
    heldPointer = event.pointerId;
    updatePlayback();
  });

  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(type => {
    viewport.addEventListener(type, event => {
      if (heldPointer !== event.pointerId) return;
      heldPointer = null;
      updatePlayback();
    });
  });

  viewport.addEventListener('keydown', event => {
    if (!animation || event.code !== 'Space') return;
    event.preventDefault();
    keyboardHeld = true;
    updatePlayback();
  });

  viewport.addEventListener('keyup', event => {
    if (event.code !== 'Space' || !keyboardHeld) return;
    event.preventDefault();
    keyboardHeld = false;
    updatePlayback();
  });

  viewport.addEventListener('blur', () => {
    keyboardHeld = false;
    updatePlayback();
  });

  viewport.addEventListener('mouseenter', () => animation?.pause());
  viewport.addEventListener('mouseleave', updatePlayback);
  viewport.addEventListener('focusin', () => animation?.pause());
  viewport.addEventListener('focusout', updatePlayback);

  reducedMotion.addEventListener('change', updateLayout);
  new ResizeObserver(updateLayout).observe(viewport);
  updateLayout();
}
