/* Shared UI. Normal forms use the backend's existing POST/redirect flow. */
'use strict';

document.querySelectorAll('[data-password-toggle]').forEach(button => {
  button.addEventListener('click', () => {
    const input = document.getElementById(button.dataset.passwordToggle);
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.textContent = show ? 'Hide' : 'Show';
    button.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    button.setAttribute('aria-pressed', String(show));
  });
});

// Submit the original POST form only after the user confirms deletion.
const confirmationElement = document.getElementById('confirm-modal');
const confirmButton = document.getElementById('confirm-action');
let pendingForm = null;
let returnFocus = null;
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', event => {
    if (form.dataset.confirmed === 'true') return;
    event.preventDefault();
    pendingForm = form;
    returnFocus = document.activeElement;
    document.getElementById('confirm-message').textContent = form.dataset.confirm;
    bootstrap.Modal.getOrCreateInstance(confirmationElement).show();
  });
});
confirmButton.addEventListener('click', () => {
  if (!pendingForm) return;
  confirmButton.disabled = true;
  pendingForm.dataset.confirmed = 'true';
  pendingForm.requestSubmit();
});
confirmationElement.addEventListener('hidden.bs.modal', () => {
  pendingForm = null;
  confirmButton.disabled = false;
  if (returnFocus && returnFocus.isConnected) returnFocus.focus();
});
// HTML autofocus does not apply to Bootstrap popups.
document.querySelectorAll('.modal').forEach(modal => {
  modal.addEventListener('shown.bs.modal', () => {
    const field = modal.id === 'confirm-modal'
      ? modal.querySelector('[data-bs-dismiss="modal"].btn-outline-secondary')
      : modal.querySelector('input:not([type="hidden"]):not(.btn-check), select, input.btn-check:checked');
    if (field) field.focus();
  });
});

// Level is a UI filter. The form sends the real backend subject_id.
const subjectSelect = document.getElementById('subject-select');
if (subjectSelect) {
  const options = Array.from(subjectSelect.querySelectorAll('option[data-level]'));
  const filterSubjects = () => {
    const level = document.querySelector('input[name="subject_level"]:checked').value;
    subjectSelect.value = '';
    options.forEach(option => {
      option.hidden = option.dataset.level !== level;
      option.disabled = option.hidden;
    });
    const available = options.some(option => !option.disabled);
    document.querySelector('#add-subject-form button[type="submit"]').disabled = !available;
    document.getElementById('subject-availability').textContent = available
      ? 'Subjects already added are omitted.' : 'All available subjects at this level have already been added.';
  };
  document.querySelectorAll('input[name="subject_level"]').forEach(radio => radio.addEventListener('change', filterSubjects));
  filterSubjects();
}

const assessmentForm = document.getElementById('assessment-form');
if (assessmentForm) {
  const score = document.getElementById('score');
  const maximum = document.getElementById('maximum-score');
  const validateScore = () => {
    const max = maximum.valueAsNumber;
    maximum.setCustomValidity(Number.isFinite(max) && max <= 0 ? 'Maximum score must be greater than zero.' : '');
    score.setCustomValidity(Number.isFinite(max) && score.valueAsNumber > max ? 'Score cannot exceed the maximum score.' : '');
  };
  [score, maximum].forEach(field => field.addEventListener('input', validateScore));
}
