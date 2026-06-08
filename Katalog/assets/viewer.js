document.querySelectorAll('.viewer-nav a').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    document.querySelectorAll('.viewer-nav a').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    const id = a.getAttribute('href').slice(1);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    const id = entry.target.id;
    document.querySelectorAll('.viewer-nav a').forEach(a => {
      a.classList.toggle('active', a.getAttribute('href') === `#${id}`);
    });
  });
}, { threshold: 0.5, rootMargin: '-52px 0px 0px 0px' });

document.querySelectorAll('.viewer-content iframe').forEach(f => observer.observe(f));
