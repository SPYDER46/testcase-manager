document.addEventListener('DOMContentLoaded', function () {
    // === Delete Modal Setup ===
    let deleteFormToSubmit = null;
    const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'), {
        backdrop: 'static',
        keyboard: false
    });
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function () {
            deleteFormToSubmit = this.closest('form');
            deleteConfirmModal.show();
        });
    });

    confirmDeleteBtn.addEventListener('click', function () {
        if (deleteFormToSubmit) {
            deleteFormToSubmit.submit();
        }
    });

    // === Summary Modal Setup ===
    const summaryModalEl = document.getElementById('summaryFormModal');
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

        // Filter out empty or '-' iterations
        const validIterations = iterations.filter(iter => iter !== '-' && iter !== '');

        // Check if all valid iteration numbers are the same AND that all testcases have valid iteration (count matches)
        const allSame = validIterations.length === iterationCells.length && validIterations.every(iter => iter === validIterations[0]);

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
});
