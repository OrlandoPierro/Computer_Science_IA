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

const subjectSelect = document.getElementById('subject-select');

if (subjectSelect) {
  const subjectId = document.getElementById('selected-subject-id');
  const levelButtons = Array.from(
    document.querySelectorAll('input[name="subject_level"]')
  );
  const submitButton = document.querySelector(
    '#add-subject-form button[type="submit"]'
  );
  const message = document.getElementById('subject-availability');

  // Send the database ID corresponding to the selected subject and level.
  function updateSubjectId() {
    const option = subjectSelect.selectedOptions[0];
    const level = levelButtons.find(
      button => button.checked && !button.disabled
    );

    subjectId.value = option && level
      ? option.dataset[level.value.toLowerCase()] || ''
      : '';

    submitButton.disabled = !subjectId.value;
  }

  // Enable only levels available for the chosen subject.
  function updateLevels() {
    const option = subjectSelect.selectedOptions[0];

    levelButtons.forEach(button => {
      const id = option?.dataset[button.value.toLowerCase()];

      button.disabled = !id;

      if (button.disabled) {
        button.checked = false;
      }
    });

    const available = levelButtons.filter(button => !button.disabled);

    // Keep the previous level when possible; otherwise select an available one.
    if (!available.some(button => button.checked) && available.length) {
      available[0].checked = true;
    }

    message.textContent = !subjectSelect.value
      ? 'Choose a subject, then select its level.'
      : available.length === 2
        ? 'Choose HL or SL below.'
        : 'Unavailable or already-added levels are disabled.';

    updateSubjectId();
  }

  subjectSelect.addEventListener('change', updateLevels);

  levelButtons.forEach(button => {
    button.addEventListener('change', updateSubjectId);
  });

  updateLevels();
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
