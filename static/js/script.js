// Enhanced script: theme toggle, form validation, OTP, modal, confetti and UI interactions

document.addEventListener('DOMContentLoaded', () => {
  // ============= ELEMENTS =============
  const themeToggle = document.getElementById('theme-toggle');
  const form = document.getElementById('appointment-form');
  const modal = document.getElementById('modal');
  const modalOk = modal ? modal.querySelector('#modal-ok') : null;
  const modalClose = modal ? modal.querySelector('.modal-close') : null;
  const formFeedback = document.getElementById('form-feedback');
  const serviceCards = document.querySelectorAll('.service-card');
  const dateInput = document.getElementById('date');
  const slotGrid = document.getElementById('slot-grid');
  const doctorSelect = document.getElementById('doctor');
  
  // OTP Elements
  const emailOtpInput = document.getElementById('email-otp');
  const sendOtpBtn = document.getElementById('send-otp-btn');
  const otpInputSection = document.getElementById('otp-input-section');
  const otpCodeInput = document.getElementById('otp-code');
  const verifyOtpBtn = document.getElementById('verify-otp-btn');
  const resendOtpBtn = document.getElementById('resend-otp-btn');
  const otpSuccessDiv = document.getElementById('otp-success');
  const mobileInput = document.getElementById('mobile');
  const otpVerifiedInput = document.getElementById('otp_verified');
  const submitBtn = document.getElementById('submit-btn');
  
  // State
  let otpVerified = false;
  let selectedSlot = null;

  // Set min date to today
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  // ============= THEME =============
  function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme) {
      document.body.classList.toggle('dark', savedTheme === 'dark');
    } else if (prefersDark) {
      document.body.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
    updateThemeButton();
  }

  let slide = 0;
  const hero = document.querySelector('.hero-overlay');

  if (hero) {
    setInterval(() => {
      slide = (slide + 2) % 2;
      hero.style.backgroundImage = slide === 0
        ? "url('/static/media/bg.png')"
        : "url('/static/media/bg2.webp')";
    }, 5000);
  }

  // Floating label support for input fields
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
    setTimeout(updateFilled, 120);
    updateFilled();
  });

  // Floating label support for select elements
  document.querySelectorAll('.field select').forEach(select => {
    const field = select.closest('.field');
    if (!field) return;
    function updateFilled(){
      if (select.value && select.value.trim() !== '') field.classList.add('filled');
      else field.classList.remove('filled');
    }
    select.addEventListener('change', updateFilled);
    select.addEventListener('focus', updateFilled);
    select.addEventListener('blur', updateFilled);
    setTimeout(updateFilled, 120);
    updateFilled();
  });

  // Theme management
  initializeTheme();
  
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      document.body.classList.toggle('dark', e.matches);
      updateThemeButton();
    }
  });
  
  themeToggle?.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
    updateThemeButton();
  });

  function updateThemeButton(){
    if(!themeToggle) return;
    themeToggle.textContent = document.body.classList.contains('dark') ? '☀️' : '🌙';
    themeToggle.setAttribute('aria-label', document.body.classList.contains('dark') ? 'Switch to light mode' : 'Switch to dark mode');
  }

  // ============= SERVICE CARDS =============
  serviceCards.forEach(card => {
    card.addEventListener('click', () => showServiceDetail(card));
    card.addEventListener('keypress', (e) => { if (e.key === 'Enter') showServiceDetail(card); });
  });

  function showServiceDetail(card){
    const title = card.querySelector('h3')?.textContent || 'Service';
    const description = card.querySelector('.service-description')?.innerHTML || 'Details coming soon.';
    showServiceModal(title, description);
  }

  // ============= MODAL =============
  function showModal(title, message){
    if (!modal) return;
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').textContent = message;
    modal.setAttribute('aria-hidden', 'false');
    modal.classList.add('open');
    if (modalOk) setTimeout(()=> modalOk.focus(), 180);
  }
  
  function showServiceModal(title, description){
    if (!modal) return;
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').innerHTML = description;
    modal.setAttribute('aria-hidden', 'false');
    modal.classList.add('open');
    if (modalOk) setTimeout(()=> modalOk.focus(), 180);
  }
  
  function hideModal(){
    if (!modal) return;
    modal.setAttribute('aria-hidden', 'true');
    modal.classList.remove('open');
  }
  
  if (modalOk) modalOk.addEventListener('click', () => hideModal());
  if (modalClose) modalClose.addEventListener('click', () => hideModal());
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape') hideModal(); });

  // ============= CONFETTI =============
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
      document.body.appendChild(el);
      setTimeout(() => el.remove(), (delay + dur) * 1000);
    }
  }

  // ============= OTP FUNCTIONALITY =============
  function clearOtpSection() {
    if (emailOtpInput) emailOtpInput.value = '';
    if (otpCodeInput) otpCodeInput.value = '';
    if (otpInputSection) otpInputSection.style.display = 'none';
    if (otpSuccessDiv) otpSuccessDiv.style.display = 'none';
  }

  if (sendOtpBtn) {
    sendOtpBtn.addEventListener('click', () => {
      const email = emailOtpInput.value.trim();
      
      if (!email || !email.includes('@')) {
        alert('Please enter a valid email address');
        return;
      }

      sendOtpBtn.disabled = true;
      sendOtpBtn.textContent = 'Sending OTP...';

      fetch('/api/send-otp/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: `email=${encodeURIComponent(email)}`
      })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          alert(`${data.message}\nFor demo: OTP is in the console/email. Check server output.`);
          if (otpInputSection) otpInputSection.style.display = 'block';
          sendOtpBtn.textContent = 'OTP Sent ✓';
        } else {
          alert(`Error: ${data.error}`);
          sendOtpBtn.textContent = 'Send OTP';
          sendOtpBtn.disabled = false;
        }
      })
      .catch(err => {
        console.error('Error:', err);
        alert('Failed to send OTP. Check console.');
        sendOtpBtn.textContent = 'Send OTP';
        sendOtpBtn.disabled = false;
      });
    });
  }

  if (verifyOtpBtn) {
    verifyOtpBtn.addEventListener('click', () => {
    const email = emailOtpInput?.value?.trim() || '';
    const otp = otpCodeInput?.value?.trim() || '';

    if (!otp || otp.length !== 6) {
      alert('Please enter a 6-digit OTP');
      return;
    }

    verifyOtpBtn.disabled = true;
    verifyOtpBtn.textContent = 'Verifying...';

    fetch('/api/verify-otp/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: `email=${encodeURIComponent(email)}&otp=${encodeURIComponent(otp)}`
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        otpVerified = true;
        // Auto-fill email in patient information section (readonly)
        const mailInput = document.getElementById('mail');
        if (mailInput) {
          mailInput.value = email;
          const field = mailInput.closest('.field');
          if (field) {
            field.classList.add('filled');
          }
        }
        if (otpVerifiedInput) otpVerifiedInput.value = 'true';
        if (otpInputSection) otpInputSection.style.display = 'none';
        if (otpSuccessDiv) {
          otpSuccessDiv.style.display = 'block';
          otpSuccessDiv.textContent = '✓ Email verified successfully';
        }
        if (submitBtn) submitBtn.disabled = false;
        if (verifyOtpBtn) verifyOtpBtn.textContent = 'Verified ✓';
      } else {
        alert(`Error: ${data.error}`);
        if (verifyOtpBtn) {
          verifyOtpBtn.textContent = 'Verify OTP';
          verifyOtpBtn.disabled = false;
        }
      }
    })
    .catch(err => {
      console.error('Error:', err);
      alert('Error verifying OTP. Check console.');
      if (verifyOtpBtn) {
        verifyOtpBtn.textContent = 'Verify OTP';
        verifyOtpBtn.disabled = false;
      }
    });
    });
  }

  if (resendOtpBtn) {
    resendOtpBtn.addEventListener('click', () => {
      clearOtpSection();
      if (sendOtpBtn) {
        sendOtpBtn.textContent = 'Send OTP';
        sendOtpBtn.disabled = false;
        sendOtpBtn.click();
      }
    });
  }

  // ============= DATE CHANGE HANDLER =============
  dateInput?.addEventListener('change', async (e) => {
    const selectedDate = e.target.value;
    if (!selectedDate) return;

    const doctorId = doctorSelect?.value || '';
    let url = `/api/booked-slots/?date=${selectedDate}`;
    if (doctorId) {
      url += `&doctor_id=${doctorId}`;
    }

    try {
      const response = await fetch(url);
      const data = await response.json();

      if (data.is_sunday) {
        alert('Clinic is closed on Sundays. Please select another date.');
        if (dateInput) dateInput.value = '';
        if (slotGrid) slotGrid.innerHTML = '<p style="color: #f44336; text-align: center; grid-column: 1/-1;">Clinic closed on Sundays</p>';
        return;
      }

      if (data.doctor_not_available) {
        alert(data.message || 'Selected doctor is not available on this date.');
        if (dateInput) dateInput.value = '';
        if (slotGrid) slotGrid.innerHTML = `<p style="color: #f44336; text-align: center; grid-column: 1/-1;">${data.message || 'Doctor not available'}</p>`;
        return;
      }

      updateSlots(data);
    } catch (err) {
      console.error('Error fetching slots:', err);
    }
  });

  // ============= DOCTOR CHANGE HANDLER =============
  doctorSelect?.addEventListener('change', async (e) => {
    // When doctor is changed, refresh the available slots for selected date
    if (dateInput && dateInput.value) {
      // Trigger date change to refresh slots
      dateInput.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });

  function updateSlots(data) {
    if (!slotGrid) return;
    slotGrid.innerHTML = '';
    selectedSlot = null;
    const timeSlotInput = document.getElementById('time_slot');
    if (timeSlotInput) timeSlotInput.value = '';

    const now = new Date();
    const today = new Date().toISOString().split('T')[0];
    const isToday = data.date === today;

    data.available_slots.forEach(slot => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'slot';
      btn.textContent = slot;
      btn.dataset.slot = slot;

      if (isToday) {
        const [time, period] = slot.split(' ');
        const [hours, minutes] = time.split(':').map(Number);
        const slotDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(),
          period === 'PM' && hours !== 12 ? hours + 12 : (period === 'AM' && hours === 12 ? 0 : hours), minutes);
        
        if (slotDate < now) {
          btn.classList.add('expired');
          btn.disabled = true;
          btn.textContent = `${slot} (Passed)`;
          slotGrid.appendChild(btn);
          return;
        }
      }

      btn.addEventListener('click', (e) => {
        e.preventDefault();
        selectSlot(btn, slot);
      });

      slotGrid.appendChild(btn);
    });

    // Show booked message if all slots booked
    if (data.available_slots.length === 0) {
      slotGrid.innerHTML = '<p style="color: #ff9800; text-align: center; grid-column: 1/-1;">All slots booked for this date</p>';
    }
  }

  function selectSlot(button, slot) {
    if (!slotGrid) return;
    const prevSelected = slotGrid.querySelector('.slot.selected');
    if (prevSelected) prevSelected.classList.remove('selected');
    
    button.classList.add('selected');
    selectedSlot = slot;
    const timeSlotInput = document.getElementById('time_slot');
    if (timeSlotInput) timeSlotInput.value = slot;
    console.log('Selected slot:', slot);
  }

  // ============= FORM SUBMISSION =============
  form?.addEventListener('submit', (e) => {
    e.preventDefault();
    clearErrors();

    const nameInput = document.getElementById('name');
    const mailInput_form = document.getElementById('mail');
    const timeSlotInput = document.getElementById('time_slot');
    const doctorInput = document.getElementById('doctor');
    const serviceInput = document.getElementById('service');

    const data = {
      name: nameInput?.value?.trim() || '',
      mail: mailInput_form?.value?.trim() || '',
      mobile: mobileInput?.value?.trim() || '',
      date: dateInput?.value || '',
      time_slot: timeSlotInput?.value || '',
      doctor_id: doctorInput?.value || '',
      service_id: serviceInput?.value || '',
      otp_verified: otpVerifiedInput?.value || 'false'
    };

    const errors = validate(data);
    if (Object.keys(errors).length) {
      showErrors(errors);
      return;
    }

    showModal('Thank you!', 'Your appointment request is received. We will contact you shortly.');
    burstConfetti();
    if (formFeedback) formFeedback.textContent = 'Submitting appointment…';

    if (window.fetch) {
      const formData = new FormData();
      formData.append('name', data.name);
      formData.append('mail', data.mail);
      formData.append('mobile', data.mobile);
      formData.append('date', data.date);
      formData.append('time_slot', data.time_slot);
      formData.append('doctor_id', data.doctor_id);
      formData.append('service_id', data.service_id);
      formData.append('otp_verified', data.otp_verified);
      formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

      fetch('/booking/', {
        method: 'POST',
        body: formData,
        headers: {'X-Requested-With': 'XMLHttpRequest'}
      })
      .then(r => r.json())
      .then(json => {
        if (json.success) {
          setTimeout(() => {
            if (form) form.reset();
            clearOtpSection();
            otpVerified = false;
            if (mobileInput) mobileInput.value = '';
            if (otpVerifiedInput) otpVerifiedInput.value = 'false';
            if (submitBtn) submitBtn.disabled = true;
            if (slotGrid) slotGrid.innerHTML = '';
            if (formFeedback) formFeedback.textContent = 'Appointment submitted successfully!';
          }, 2000);
        } else {
          if (formFeedback) formFeedback.textContent = 'Error: ' + (json.error || 'Unknown error');
        }
      })
      .catch(err => {
        console.error(err);
        if (formFeedback) formFeedback.textContent = 'Submission failed. Check console.';
      });
    } else {
      if (form) form.submit();
    }
  });

  function validate(data) {
    const errors = {};
    if (!data.name || data.name.length < 2) errors.name = 'Enter a valid name';
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(data.mail)) errors.mail = 'Enter a valid email';
    if (!/^\d{10}$/.test(data.mobile.replace(/[^0-9]/g, ''))) errors.mobile = 'Enter a valid 10-digit phone';
    if (!data.date) errors.date = 'Select a date';
    if (!data.time_slot) errors.time_slot = 'Select a time slot';
    if (data.otp_verified !== 'true') errors.otp = 'Verify phone with OTP';
    return errors;
  }

  function showErrors(errors) {
    Object.entries(errors).forEach(([k, msg]) => {
      const el = document.querySelector(`.error[data-for="${k}"]`);
      if (el) el.textContent = msg;
      const input = document.getElementById(k);
      if (input) input.setAttribute('aria-invalid', 'true');
    });
  }

  function clearErrors() {
    document.querySelectorAll('.error').forEach(e => e.textContent = '');
    document.querySelectorAll('input, select').forEach(i => i.removeAttribute('aria-invalid'));
    formFeedback.textContent = '';
  }

  // ============= PHONE FORMATTING =============
  mobileInput?.addEventListener('input', (e) => {
    e.target.value = e.target.value.replace(/[^0-9]/g, '').slice(0, 10);
  });

  // ============= SCROLL SPY =============
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = Array.from(navLinks)
    .map(a => {
      const href = a.getAttribute('href') || '';
      // Only treat in-page anchors (starting with '#') as selectors
      if (!href || !href.startsWith('#') || href === '#') return null;
      try {
        return document.querySelector(href);
      } catch (err) {
        // If someone accidentally used a non-selector href (like '/'), skip it and warn
        console.warn('Invalid selector in nav link href:', href, err);
        return null;
      }
    })
    .filter(Boolean);

  window.addEventListener('scroll', () => {
    let idx = sections.findIndex((s, i) => {
      const rect = s.getBoundingClientRect();
      return rect.top <= 100 && rect.bottom >= 100;
    });
    navLinks.forEach(l => l.classList.remove('active'));
    if(idx >= 0 && navLinks[idx]) navLinks[idx].classList.add('active');
  });

  // ============= REVEAL ANIMATIONS =============
  const revealElements = document.querySelectorAll('.reveal');
  if (revealElements.length > 0 && 'IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          revealObserver.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    });

    revealElements.forEach(el => revealObserver.observe(el));
  }

  // Helper function
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }
});

// Scroll to appointment
function scrollToAppointment() {
  const appointmentSection = document.getElementById('appointment');
  if (appointmentSection) {
    appointmentSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// API Service
const AppointmentService = {
  book: (data) => {
    console.log('Appointment Data:', data);
  }
};

// ============= FEEDBACK SECTION =============
document.addEventListener('DOMContentLoaded', () => {
  const feedbackForm = document.getElementById('feedback-form');
  const feedbackStatus = document.getElementById('feedback-status');
  const feedbackTestimonial = document.getElementById('feedback-testimonial');

  if (feedbackForm) {
    feedbackForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const name = document.getElementById('feedback-name').value.trim();
      const message = document.getElementById('feedback-message').value.trim();
      
      if (!name || !message) {
        feedbackStatus.textContent = 'Please fill in all fields';
        feedbackStatus.style.color = 'red';
        return;
      }

      feedbackStatus.textContent = 'Submitting feedback...';
      feedbackStatus.style.color = '#2fa4a9';

      try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('message', message);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

        const response = await fetch('/api/submit-feedback/', {
          method: 'POST',
          body: formData
        });

        const data = await response.json();

        if (data.success) {
          feedbackStatus.textContent = data.message;
          feedbackStatus.style.color = 'green';
          feedbackForm.reset();
          
          // Display the new feedback in the feedback section
          displayNewFeedback(data.feedback);
          
          // Reload all feedback and testimonials
          loadAllFeedback();
          
          setTimeout(() => {
            feedbackStatus.textContent = '';
          }, 3000);
        } else {
          feedbackStatus.textContent = 'Error: ' + (data.error || 'Unknown error');
          feedbackStatus.style.color = 'red';
        }
      } catch (error) {
        console.error('Feedback submission error:', error);
        feedbackStatus.textContent = 'An error occurred. Please try again.';
        feedbackStatus.style.color = 'red';
      }
    });

    // Load existing feedback on page load
    loadAllFeedback();
  }
});

function displayNewFeedback(feedback) {
  const feedbackTestimonial = document.getElementById('feedback-testimonial');
  if (feedbackTestimonial) {
    const feedbackBox = document.createElement('blockquote');
    feedbackBox.className = 'feedback-box';
    feedbackBox.innerHTML = `
      <p>"${feedback.message}"</p>
      <cite>— ${feedback.name}</cite>
    `;
    
    // Clear placeholder if it exists
    const placeholder = feedbackTestimonial.querySelector('.feedback-placeholder');
    if (placeholder) {
      placeholder.remove();
    }
    
    feedbackTestimonial.appendChild(feedbackBox);
  }
}

function loadAllFeedback() {
  fetch('/api/get-feedback/')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.feedbacks.length > 0) {
        // Update testimonials section
        updateTestimonials(data.feedbacks);
        
        // Update feedback display box
        updateFeedbackDisplay(data.feedbacks);
      }
    })
    .catch(error => console.error('Error loading feedback:', error));
}

function updateTestimonials(feedbacks) {
  const testimonialsGrid = document.querySelector('.testimonials-grid');
  if (testimonialsGrid) {
    // Add feedback as testimonials
    feedbacks.forEach(feedback => {
      // Check if feedback already exists
      const existingFeedback = testimonialsGrid.querySelector(`[data-feedback-id="${feedback.id}"]`);
      if (!existingFeedback) {
        const testimonialBlock = document.createElement('blockquote');
        testimonialBlock.className = 'testimonial';
        testimonialBlock.setAttribute('data-feedback-id', feedback.id);
        const rating = feedback.rating ? '(' + feedback.rating + '/5 ★)' : '';
        testimonialBlock.innerHTML = `
          <p>"${feedback.feedback_text || feedback.message}"</p>
          <cite>— ${feedback.name} ${rating}</cite>
        `;
        testimonialsGrid.appendChild(testimonialBlock);
      }
    });
  }
}

function updateFeedbackDisplay(feedbacks) {
  const feedbackTestimonial = document.getElementById('feedback-testimonial');
  if (feedbackTestimonial) {
    feedbackTestimonial.innerHTML = '';
    
    if (!feedbacks || feedbacks.length === 0) {
      feedbackTestimonial.innerHTML = '<p style="text-align: center; color: #999;">No feedback yet. Be the first to share!</p>';
      return;
    }
    
    feedbacks.slice(0, 3).forEach(feedback => {
      const feedbackBox = document.createElement('blockquote');
      feedbackBox.className = 'feedback-box';
      feedbackBox.style.cssText = 'background: #f9f9f9; padding: 16px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #2fa4a9; line-height: 1.6;';
      const rating = feedback.rating ? '★ ' + feedback.rating + '/5' : '';
      feedbackBox.innerHTML = `
        <p style="margin: 0 0 8px 0; font-style: italic; color: #333;">"${feedback.feedback_text || feedback.message}"</p>
        <cite style="color: #666; font-size: 13px;">— ${feedback.name}</cite>
        ${rating ? '<div style="margin-top: 6px; color: #2fa4a9; font-size: 13px;">' + rating + '</div>' : ''}
      `;
      feedbackTestimonial.appendChild(feedbackBox);
    });
  }
}
