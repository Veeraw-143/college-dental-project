// Enhanced script: theme toggle, form validation, modal, confetti and small UI interactions

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const themeToggle = document.getElementById('theme-toggle');
  const form = document.getElementById('appointment-form');
  const modal = document.getElementById('modal');
  const modalOk = document.getElementById('modal-ok');
  const modalClose = document.querySelector('.modal-close');
  const formFeedback = document.getElementById('form-feedback');
  const serviceCards = document.querySelectorAll('.service-card');
  const dateInput = document.getElementById('date');

  // Set min date to today
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  // Floating label support: keep label lifted when field has value
  document.querySelectorAll('.field input[type="text"], .field input[type="email"], .field input[type="tel"], .field input[type="date"]').forEach(input => {
    const field = input.closest('.field');
    if (!field) return;
    function updateFilled(){
      if (input.value && input.value.trim() !== '') field.classList.add('filled');
      else field.classList.remove('filled');
    }
    input.addEventListener('input', updateFilled);
    input.addEventListener('focus', updateFilled);
    input.addEventListener('blur', updateFilled);
    // run once in case autofill filled the inputs
    setTimeout(updateFilled, 120);
    updateFilled();
  });

  // Theme management
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') document.body.classList.add('dark');
  updateThemeButton();
  themeToggle?.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
    updateThemeButton();
  });

  function updateThemeButton(){
    if(!themeToggle) return;
    themeToggle.textContent = document.body.classList.contains('dark') ? '☀️' : '🌙';
  }

  // Smooth scroll helper used by inline onclick
  window.scrollToAppointment = () => document.getElementById('appointment').scrollIntoView({behavior:'smooth'});

  // Reveal-on-scroll using IntersectionObserver
  const revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    const obs = new IntersectionObserver((entries)=>{
      entries.forEach(e=>{
        if(e.isIntersecting){
          e.target.classList.add('in-view');
          obs.unobserve(e.target);
        }
      });
    },{threshold:0.08});
    revealEls.forEach(el=>obs.observe(el));
  } else { // fallback
    revealEls.forEach(el=>el.classList.add('in-view'));
  }

  // Helper: read cookie (for CSRF)
  function getCookie(name){
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }

  // Service card interactions
  serviceCards.forEach(card => {
    card.addEventListener('click', () => showServiceDetail(card));
    card.addEventListener('keypress', (e) => { if (e.key === 'Enter') showServiceDetail(card); });
  });

  function showServiceDetail(card){
    const title = card.querySelector('h3')?.textContent || 'Service';
    showModal(title, card.querySelector('p')?.textContent || 'Details coming soon.');
  }

  // Modal helpers (animated)
  function showModal(title, message){
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').textContent = message;
    modal.setAttribute('aria-hidden', 'false');
    modal.classList.add('open');
    // focus after the opening animation starts
    setTimeout(()=> modalOk.focus(), 180);
  }
  function hideModal(){
    modal.setAttribute('aria-hidden', 'true');
    modal.classList.remove('open');
  }
  modalOk.addEventListener('click', () => hideModal());
  modalClose.addEventListener('click', () => hideModal());
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape') hideModal(); });

  // Simple confetti (with random delay/duration for a smoother feel)
  function burstConfetti(){
    for(let i=0;i<24;i++){
      const el = document.createElement('div');
      el.className = 'confetti';
      const delay = Math.random()*0.35;
      const dur = 1.6 + Math.random()*0.8;
      el.style.left = Math.random()*100 + '%';
      el.style.background = ['#FFB4A2','#F08A5D','#F9ED69','#A8D0E6','#9BF6FF'][Math.floor(Math.random()*5)];
      el.style.transform = `translateY(${-(Math.random()*20+10)}px) rotate(${Math.random()*360}deg)`;
      el.style.animationDelay = `${delay}s`;
      el.style.animationDuration = `${dur}s`;
      el.style.willChange = 'transform, opacity';
      document.body.appendChild(el);
      setTimeout(()=> el.remove(), (dur + delay) * 1000 + 200);
    }
  }

  // Form validation and submission handling
  form?.addEventListener('submit', (e) => {
    // prevent default to provide a friendly UI then let the form submit after a short delay
    e.preventDefault();
    clearErrors();
    const data = {
      name: form.name.value.trim(),
      mail: form.mail.value.trim(),
      mobile: form.mobile.value.trim(),
      date: form.date.value,
      time: form.time.value
    };

    const errors = validate(data);
    if (Object.keys(errors).length){
      showErrors(errors);
      formFeedback.textContent = 'Please fix the highlighted fields.';
      return;
    }

    // show a success modal and animate confetti, then submit the native form to backend
    showModal('Thank you!', 'Your appointment request is received. We will contact you shortly.');
    burstConfetti();
    formFeedback.textContent = 'Submitting appointment…';

    // If fetch is supported, do AJAX submit for a smoother UX (falls back to native submit)
    if (window.fetch){
      const action = form.action;
      const fd = new FormData(form);
      const csrf = getCookie('csrftoken') || getCookie('csrf');
      fetch(action, {
        method:'POST',
        headers:{
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrf,
          'Accept': 'application/json'
        },
        body: fd,
        credentials: 'same-origin'
      }).then(res => {
        const ct = res.headers.get('content-type') || '';
        if (ct.indexOf('application/json') !== -1) return res.json();
        return res.text().then(t => ({html:t}));
      }).then(data => {
        if (data && data.success){
          showModal('Thank you!', data.message || 'Your appointment request is received.');
          burstConfetti();
          formFeedback.textContent = data.message || 'Submitted';
          form.reset();
          document.querySelectorAll('.field').forEach(f=>f.classList.remove('filled'));
        } else {
          // map server errors to fields if provided
          if (data && data.errors){
            showErrors(data.errors);
            formFeedback.textContent = data.message || 'Please fix the fields below.';
          } else if (data && data.error){
            formFeedback.textContent = data.error;
          } else {
            // fallback: submit the native form
            setTimeout(()=> form.submit(), 900);
          }
        }
      }).catch(()=> {
        // network or parse error -> fallback to native submit
        setTimeout(()=> form.submit(), 900);
      });
    } else {
      setTimeout(()=> form.submit(), 900);
    }
  });

  function validate({name, mail, mobile, date, time}){
    const errors = {};
    if (!name || name.length < 2) errors.name = 'Enter a valid name (min 2 chars)';
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(mail)) errors.mail = 'Provide a valid email';
    if (!/^\+?[0-9]{7,15}$/.test(mobile.replace(/[^0-9+]/g,''))) errors.mobile = 'Enter a valid phone number';
    if (!date) errors.date = 'Pick a date';
    else {
      const today = new Date().toISOString().split('T')[0];
      if (date < today) errors.date = 'Date cannot be in the past';
    }
    if (!time) errors.time = 'Select a time';
    return errors;
  }

  function showErrors(errors){
    Object.entries(errors).forEach(([k,msg])=>{
      const el = document.querySelector(`.error[data-for="${k}"]`);
      if(el) el.textContent = msg;
      const input = document.getElementById(k);
      if(input) input.setAttribute('aria-invalid', 'true');
    });
  }
  function clearErrors(){
    document.querySelectorAll('.error').forEach(e=>e.textContent='');
    document.querySelectorAll('.appointment-card input').forEach(i=>i.removeAttribute('aria-invalid'));
    formFeedback.textContent = '';
  }

  // Phone formatting (simple)
  const mobileInput = document.getElementById('mobile');
  mobileInput?.addEventListener('input', (e)=>{
    const cleaned = e.target.value.replace(/[^0-9+]/g, '');
    // simple groups: +CC (optional) then groups of 3-4
    e.target.value = cleaned;
  });

  // tiny scrollspy to highlight nav
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = Array.from(navLinks).map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
  window.addEventListener('scroll', () => {
    let idx = sections.findIndex((s, i) => {
      const rect = s.getBoundingClientRect();
      return rect.top <= 120 && rect.bottom > 160;
    });
    navLinks.forEach(l=> l.classList.remove('active'));
    if(idx>=0 && navLinks[idx]) navLinks[idx].classList.add('active');
  });

});

// Expose a minimal API for potential reuse
const AppointmentService = {
  book: (data) => {
    console.log('Appointment Data:', data);
    // can be extended to call backend via fetch
  }
};
