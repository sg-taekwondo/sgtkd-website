
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle) toggle.addEventListener('click', () => links.classList.toggle('open'));

  const path = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a[data-page]').forEach(a => {
    if (a.getAttribute('data-page') === path) a.classList.add('active');
  });

  document.querySelectorAll('form[data-demo]').forEach(form => {
    form.addEventListener('submit', e => {
      e.preventDefault();
      alert('Thanks! This demo form is ready to connect to your preferred email/form service.');
      form.reset();
    });
  });
});
// Always start the homepage at the top
if (window.location.pathname.endsWith('/index.html') || window.location.pathname.endsWith('/sgtkd-website/')) {
    window.addEventListener('load', function () {
        window.scrollTo(0, 0);
    });
}
