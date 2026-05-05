(function () {
  const toggle = document.getElementById('mobileMenuToggle');
  const nav = document.getElementById('siteNav');
  const backdrop = document.getElementById('mobileNavBackdrop');

  if (!toggle || !nav || !backdrop) return;

  const mobileQuery = window.matchMedia('(max-width: 768px)');
  let lockedScrollY = 0;

  function readLockedScrollY() {
    const top = document.body.style.top;
    if (!top) return 0;
    const value = parseInt(top, 10);
    if (!Number.isFinite(value)) return 0;
    return Math.abs(value);
  }

  function lockScroll() {
    // iOS-friendly scroll lock: avoid background scroll + layout shift.
    lockedScrollY = window.scrollY || 0;
    document.body.style.position = 'fixed';
    document.body.style.top = `-${lockedScrollY}px`;
    document.body.style.left = '0';
    document.body.style.right = '0';
    document.body.style.width = '100%';
  }

  function unlockScroll() {
    if (document.body.style.position !== 'fixed') return;

    const restoreY = lockedScrollY || readLockedScrollY();

    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.left = '';
    document.body.style.right = '';
    document.body.style.width = '';

    lockedScrollY = 0;
    window.scrollTo(0, restoreY);
  }

  function setOpen(isOpen) {
    if (isOpen) lockScroll();
    else unlockScroll();

    document.body.classList.toggle('mobile-nav-open', isOpen);
    toggle.setAttribute('aria-expanded', String(isOpen));
    toggle.setAttribute('aria-label', isOpen ? 'Close menu' : 'Open menu');
    backdrop.hidden = !isOpen;
  }

  function closeMenu() {
    setOpen(false);
  }

  function toggleMenu() {
    if (!mobileQuery.matches) return;
    setOpen(!document.body.classList.contains('mobile-nav-open'));
  }

  toggle.addEventListener('click', toggleMenu);
  backdrop.addEventListener('click', closeMenu);

  nav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', closeMenu);
  });

  const logoutButton = nav.querySelector('.logout-link-btn');
  if (logoutButton) {
    logoutButton.addEventListener('click', closeMenu);
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });

  mobileQuery.addEventListener('change', (event) => {
    if (!event.matches) {
      closeMenu();
      backdrop.hidden = true;
    }
  });

  // Always start closed (including BFCache restores).
  setOpen(false);
  window.addEventListener('pageshow', closeMenu);
})();
