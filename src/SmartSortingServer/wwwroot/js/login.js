const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const loginButton = document.getElementById('loginButton');

loginForm.addEventListener('submit', async event => {
  event.preventDefault();

  const loginId = document.getElementById('adminId').value.trim();
  const password = document.getElementById('adminPassword').value.trim();

  if (!loginId || !password) {
    loginError.textContent = '아이디와 비밀번호를 입력하세요.';
    return;
  }

  loginError.textContent = '';
  loginButton.disabled = true;
  loginButton.textContent = '로그인 중...';

  try {
    await login(loginId, password);
    window.location.href = 'index.html';
  } catch (error) {
    console.error(error);
    loginError.textContent = '아이디 또는 비밀번호를 확인하세요.';
  } finally {
    loginButton.disabled = false;
    loginButton.textContent = '로그인';
  }
});

const passwordInput = document.getElementById('adminPassword');
const passwordToggle = document.getElementById('passwordToggle');

passwordToggle?.addEventListener('click', () => {
  const isPassword = passwordInput.type === 'password';

  passwordInput.type = isPassword ? 'text' : 'password';
  passwordToggle.innerHTML = isPassword
    ? '<i data-lucide="eye-off"></i>'
    : '<i data-lucide="eye"></i>';

  lucide.createIcons();
});