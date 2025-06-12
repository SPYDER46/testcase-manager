document.addEventListener('DOMContentLoaded', function () {
    // === Delete Confirmation Modal ===
    const deleteConfirmModalEl = document.getElementById('deleteConfirmModal');
    const deleteConfirmForm = document.getElementById('deleteConfirmForm');
    const deleteConfirmModal = deleteConfirmModalEl ? new bootstrap.Modal(deleteConfirmModalEl, {
        backdrop: 'static',
        keyboard: false
    }) : null;
    const deleteConfirmMessage = document.getElementById('deleteConfirmMessage');

    let currentForm = null;

    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function () {
            const deleteUrl = this.getAttribute('data-url');
            const itemType = this.getAttribute('data-item') || 'item'; // new attribute to distinguish type

            if (deleteConfirmForm && deleteConfirmModal && deleteUrl) {
                deleteConfirmForm.action = deleteUrl;

                // Update modal message depending on item type
               if (itemType === 'suite') {
                    deleteConfirmMessage.textContent = "Are you sure you want to delete this Test cases? This action cannot be undone.";
                } else if (itemType === 'iteration') {
                    deleteConfirmMessage.textContent = "Are you sure you want to delete this iteration? This action cannot be undone.";
                } else if (itemType === 'testcase') {
                    deleteConfirmMessage.textContent = "Are you sure you want to delete this Test Plan? This action cannot be undone.";
                } else {
                    deleteConfirmMessage.textContent = "Are you sure you want to delete this item? This action cannot be undone.";
                }
                currentForm = this.closest('form');
                deleteConfirmModal.show();
            }
        });
    });

    deleteConfirmForm.addEventListener('submit', function (e) {
        e.preventDefault();
        if (currentForm) {
            currentForm.submit();
        }
    });


    // === Summary Modal Setup ===
    const summaryModalEl = document.getElementById('summaryFormModal');
    if (summaryModalEl) {
        const summaryModal = new bootstrap.Modal(summaryModalEl, {
            backdrop: 'static',
            keyboard: false
        });

        const openSummaryBtn = document.getElementById('openSummaryModalBtn');
        if (openSummaryBtn) {
            openSummaryBtn.addEventListener('click', function () {
                summaryModal.show();
            });
        }

        // Automatically set iteration_no input when modal opens
        summaryModalEl.addEventListener("show.bs.modal", function () {
        const iterationInput = document.querySelector("input[name='iteration_no']");
        if (iterationInput) {
            const iterationCell = document.querySelector("td.iteration");
            if (iterationCell) {
                const iterationNumber = iterationCell.textContent.trim();
                iterationInput.value = iterationNumber || '';
            } else {
                iterationInput.value = '';
            }
        }
    });

    }

    // === Add Test Suite Modal Setup ===
    const suiteModalEl = document.getElementById('testSuiteModal');
    if (suiteModalEl) {
        const suiteModal = new bootstrap.Modal(suiteModalEl, {
            backdrop: 'static',
            keyboard: false
        });
    }

    // === Toast Setup ===
    const toastEl = document.getElementById('deleteToast');
    if (toastEl) {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }

    // === Enable "Complete Testing" button if all iteration statuses are filled and the same ===
    const iterationCells = document.querySelectorAll('td.iteration');
    const completeBtn = document.getElementById('openSummaryModalBtn');

    if (completeBtn && iterationCells.length > 0) {
        const iterations = Array.from(iterationCells).map(cell => cell.textContent.trim());
        const validIterations = iterations.filter(iter => iter !== '-' && iter !== '');
        const allSame = validIterations.length === iterationCells.length &&
                        validIterations.every(iter => iter === validIterations[0]);
        completeBtn.disabled = !allSame;
    }

    // === Page Loader Fade Out ===
    window.addEventListener('load', () => {
        const loader = document.getElementById('page-loader');
        if (loader) {
            loader.classList.add('fade-out');
            setTimeout(() => loader.style.display = 'none', 500);
        }
    });

    // === Download PDF Report ===
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', () => {
            console.log('Download PDF button clicked');

            const report = document.getElementById('report-content');
            if (!report) {
                alert('Report content not found!');
                console.error('No element with id "report-content" found.');
                return;
            }

            html2canvas(report, { scale: 2 }).then(canvas => {
                console.log('Canvas created from report-content');

                const imgData = canvas.toDataURL('image/png');
                const { jsPDF } = window.jspdf;
                const doc = new jsPDF();

                doc.addImage(imgData, 'PNG', 10, 10, 180, 0);
                doc.save('Testing_Summary.pdf');
                console.log('PDF saved');
            }).catch(err => {
                console.error('Error generating PDF:', err);
                alert('Failed to generate PDF. See console for details.');
            });
        });
    } else {
        console.warn('Download PDF button (#downloadPdfBtn) not found.');
    }

    // === CSV Upload Form Handler ===
    const csvUploadForm = document.getElementById('csvUploadForm');
    if (csvUploadForm) {
        csvUploadForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const fileInput = csvUploadForm.querySelector('input[name="file"]');
            const uploadStatus = document.getElementById('uploadStatus');
            uploadStatus.textContent = '';
            uploadStatus.style.color = '';

            if (!fileInput.files.length) {
                uploadStatus.textContent = 'Please select a CSV file.';
                uploadStatus.style.color = 'red';
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            const gameName = document.getElementById('gameName')?.value || 'DefaultGameName';
            formData.append('game', gameName);

            try {
                const response = await fetch('/upload_testcases', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    uploadStatus.textContent = `Success! Imported ${result.added.length} test cases.`;
                    uploadStatus.style.color = 'green';
                    setTimeout(() => location.reload(), 1500);
                } else {
                    uploadStatus.textContent = `Error: ${result.error || 'Failed to upload'}`;
                    uploadStatus.style.color = 'red';
                }
            } catch (err) {
                uploadStatus.textContent = 'Upload failed: ' + err.message;
                uploadStatus.style.color = 'red';
            }
        });
    }

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('error') === 'duplicate') {
        const customAlert = document.getElementById('customAlert');
        if (customAlert) {
            customAlert.style.display = 'block';
        }

        // Remove error param so alert doesn't reappear on reload
        const url = new URL(window.location);
        url.searchParams.delete('error');
        window.history.replaceState({}, document.title, url.toString());
    }
});


function filterGames() {
  const input = document.getElementById('searchInput').value.toLowerCase();
  const cards = document.querySelectorAll('.game-card');

  cards.forEach(card => {
    const name = card.querySelector('h5').textContent.toLowerCase();
    card.style.display = name.includes(input) ? '' : 'none';
  });
}

  document.getElementById('searchInput').addEventListener('input', function () {
    const query = this.value.toLowerCase();
    const cards = document.querySelectorAll('.game-card');

    cards.forEach(card => {
      const name = card.textContent.toLowerCase();
      card.style.display = name.includes(query) ? 'block' : 'none';
    });
  });


// Add Game function
document.addEventListener('DOMContentLoaded', function () {
  // Helper function to update button text for a dropdown
  function updateDropdownText(dropdownId, buttonId, placeholder) {
    const dropdown = document.getElementById(dropdownId);
    const button = document.getElementById(buttonId);
    const radios = dropdown.querySelectorAll('input[type="radio"]');

    let selectedLabel = '';
    radios.forEach(radio => {
      if (radio.checked) {
        const label = dropdown.querySelector(`label[for="${radio.id}"]`);
        if (label) selectedLabel = label.textContent.trim();
      }
    });

    button.textContent = selectedLabel || placeholder;
  }

  // Attach listeners to radio inputs for phases dropdown
  const phasesMenu = document.getElementById('gamePhaseDropdownMenu');
  if (phasesMenu) {
    phasesMenu.querySelectorAll('input[type="radio"]').forEach(radio => {
      radio.addEventListener('change', () => {
        updateDropdownText('gamePhaseDropdownMenu', 'gamePhaseDropdown', 'Select Phases');
      });
    });
  }

  // Attach listeners to radio inputs for categories dropdown
  const categoriesMenu = document.getElementById('gameCategoryDropdownMenu');
  if (categoriesMenu) {
    categoriesMenu.querySelectorAll('input[type="radio"]').forEach(radio => {
      radio.addEventListener('change', () => {
        updateDropdownText('gameCategoryDropdownMenu', 'gameCategoryDropdown', 'Select Categories');
      });
    });
  }

  // Initial call to set button text properly on load
  updateDropdownText('gamePhaseDropdownMenu', 'gamePhaseDropdown', 'Select Phases');
  updateDropdownText('gameCategoryDropdownMenu', 'gameCategoryDropdown', 'Select Categories');
});

var addGameModal = new bootstrap.Modal(document.getElementById('addGameModal'), {
  backdrop: 'static',
  keyboard: false
});


function filterGames() {
  const searchInput = document.getElementById('searchInput').value.toLowerCase();
  const phaseFilter = document.getElementById('filterPhase').value;
  const categoryFilter = document.getElementById('filterCategory').value;

  const gameCards = document.querySelectorAll('.game-card');

  gameCards.forEach(card => {
    const gameName = card.querySelector('h5').textContent.toLowerCase();

    // Assuming each card has data attributes for phase and category for filtering, e.g.:
    // <div class="game-card" data-phase="Phase 1" data-category="Turbo">
    const gamePhase = card.getAttribute('data-phase') || '';
    const gameCategory = card.getAttribute('data-category') || '';

    // Check filters
    const matchesSearch = gameName.includes(searchInput);
    const matchesPhase = phaseFilter === '' || gamePhase === phaseFilter;
    const matchesCategory = categoryFilter === '' || gameCategory === categoryFilter;

    if (matchesSearch && matchesPhase && matchesCategory) {
      card.style.display = '';
    } else {
      card.style.display = 'none';
    }
  });
}




// Clear all filters and search, then show all games
document.getElementById('clearBtn').addEventListener('click', () => {
  // Clear search input
  document.getElementById('searchInput').value = '';

  // Reset filter selects
  document.getElementById('filterPhase').value = '';
  document.getElementById('filterCategory').value = '';

  // Optionally close filter panel if open
  const filterPanel = document.getElementById('filterPanel');
  if (filterPanel.classList.contains('show')) {
    const bsCollapse = bootstrap.Collapse.getInstance(filterPanel);
    if (bsCollapse) bsCollapse.hide();
  }

  // Run filter function to reset display
  filterGames();
});


 function confirmDelete(button) {
    const name = button.getAttribute('data-game-name');
    return confirm(`Are you sure you want to delete ${name}?`);
  }


// Login page
 function confirmLogout() {
    return confirm("Are you sure you want to log out?");
  }

function togglePassword() {
    const passwordInput = document.getElementById("password");
    const type = passwordInput.getAttribute("type");
    passwordInput.setAttribute("type", type === "password" ? "text" : "password");
  }



 const confirmDeleteModal = document.getElementById('confirmDeleteModal');
  confirmDeleteModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget;
    const gameName = button.getAttribute('data-game-name');

    // Update modal game name
    const gameToDeleteName = confirmDeleteModal.querySelector('#gameToDeleteName');
    gameToDeleteName.textContent = gameName;

    // Update form action
    const deleteForm = confirmDeleteModal.querySelector('#deleteGameForm');
    deleteForm.action = `/delete/${encodeURIComponent(gameName)}`;
  });

// Flash popup
    setTimeout(() => {
    const alerts = document.querySelectorAll('#flash-container .alert');
    alerts.forEach(alert => {
      // Use Bootstrap's fade class
      alert.classList.remove('show');
      alert.classList.add('fade');
      setTimeout(() => alert.remove(), 300); 
    });
  }, 3000);

  // Register form -------------------
  const form = document.getElementById('registerForm');
  const modal = document.getElementById('roleModal');
  const orgInput = document.getElementById('orgInput');
  const roleInput = document.getElementById('roleInput');
  const confirmBtn = document.getElementById('confirmBtn');
  const closeModal = document.getElementById('closeModal');

  const username = document.getElementById('username');
  const email = document.getElementById('email');
  const password = document.getElementById('password');
  const submitBtn = document.getElementById('submitBtn');

  const usernameError = document.getElementById('usernameError');
  const emailError = document.getElementById('emailError');
  const passwordError = document.getElementById('passwordError');

  // Show error under input
  function showError(input, errorElem, message) {
    input.classList.add('invalid');
    errorElem.textContent = message;
  }

  // Clear error
  function clearError(input, errorElem) {
    input.classList.remove('invalid');
    errorElem.textContent = '';
  }

  // Validate form fields
  function validateForm(showMessages = false) {
    let isValid = true;

    if (!username.value.trim()) {
      if (showMessages) showError(username, usernameError, 'Username is required');
      isValid = false;
    } else {
      clearError(username, usernameError);
    }

    if (!email.value.trim()) {
      if (showMessages) showError(email, emailError, 'Email is required');
      isValid = false;
    } else if (!email.validity.valid) {
      if (showMessages) showError(email, emailError, 'Enter a valid email');
      isValid = false;
    } else {
      clearError(email, emailError);
    }

    if (!password.value.trim()) {
      if (showMessages) showError(password, passwordError, 'Password is required');
      isValid = false;
    } else {
      clearError(password, passwordError);
    }

    submitBtn.disabled = !isValid;
    return isValid;
  }

  // Enable/disable Submit as user types
  [username, email, password].forEach(input => {
  input.addEventListener('input', () => validateForm(false));
  input.addEventListener('change', () => validateForm(false));
});


  // When form is submitted
form.addEventListener('submit', function (e) {
  e.preventDefault();

  // Re-validate on submit click
  if (validateForm(true)) {

    if (modal.style.display !== 'flex') {
      modal.style.display = 'flex';
    }
  }
});

  // Close modal with × button
  closeModal.addEventListener('click', () => {
    modal.style.display = 'none';
  });

  // Final modal submit
  confirmBtn.addEventListener('click', () => {
    if (!orgInput.value.trim() || !roleInput.value) {
      alert('Please fill out organization and role.');
      return;
    }

    const orgHidden = document.createElement('input');
    orgHidden.type = 'hidden';
    orgHidden.name = 'organization';
    orgHidden.value = orgInput.value;

    const roleHidden = document.createElement('input');
    roleHidden.type = 'hidden';
    roleHidden.name = 'role';
    roleHidden.value = roleInput.value;

    form.appendChild(orgHidden);
    form.appendChild(roleHidden);

    modal.style.display = 'none';
    form.submit(); // Final form submission
  });

  // Validate on page load (optional)
  window.addEventListener('load', () => {
    validateForm(false); // Catch autofill on load
  });
