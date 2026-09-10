const adminDropdown = document.querySelector('.admin-dropdown');
const adminMenuButton = document.getElementById('adminMenuButton');
const logoutMenuButton = document.getElementById('logoutMenuButton');
const adminNameElement = document.getElementById('adminName');

const logoutModal = document.getElementById('logoutModal');
const cancelLogoutButton = document.getElementById('cancelLogoutButton');
const confirmLogoutButton = document.getElementById('confirmLogoutButton');

const adminName = localStorage.getItem('adminName');
adminMenuButton?.setAttribute('aria-controls', 'adminDropdownMenu');
adminMenuButton?.setAttribute('aria-expanded', 'false');

function setAdminMenuOpen(open) {
  adminDropdown?.classList.toggle('open', open);
  adminMenuButton?.setAttribute('aria-expanded', String(open));
}

if (adminName && adminNameElement) {
  adminNameElement.textContent = adminName;
}

adminMenuButton?.addEventListener('click', event => {
  event.stopPropagation();
  setAdminMenuOpen(!adminDropdown.classList.contains('open'));
});

document.addEventListener('click', () => {
  setAdminMenuOpen(false);
});

adminDropdown?.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    setAdminMenuOpen(false);
    adminMenuButton?.focus();
  } else if (event.key === 'ArrowDown') {
    event.preventDefault();
    setAdminMenuOpen(true);
    logoutMenuButton?.focus();
  }
});

adminDropdown?.addEventListener('focusout', event => {
  if (!adminDropdown.contains(event.relatedTarget)) setAdminMenuOpen(false);
});

logoutMenuButton?.addEventListener('click', event => {
  event.stopPropagation();
  setAdminMenuOpen(false);
  logoutModal.hidden = false;
});

cancelLogoutButton?.addEventListener('click', () => {
  logoutModal.hidden = true;
});

logoutModal?.addEventListener('click', event => {
  if (event.target === logoutModal) {
    logoutModal.hidden = true;
  }
});

confirmLogoutButton?.addEventListener('click', () => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('adminName');
  window.location.href = 'login.html';
});
