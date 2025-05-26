document.addEventListener('DOMContentLoaded', function() {
    // Delete modal setup
    let deleteFormToSubmit = null;
    const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'), {
        backdrop: 'static',
        keyboard: false
    });
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function() {
            deleteFormToSubmit = this.closest('form');
            deleteConfirmModal.show();
        });
    });

    confirmDeleteBtn.addEventListener('click', function() {
        if (deleteFormToSubmit) {
            deleteFormToSubmit.submit();
        }
        deleteConfirmModal.hide();
    });

    // Summary modal setup
    const summaryModalEl = document.getElementById('summaryFormModal');
    const summaryModal = new bootstrap.Modal(summaryModalEl, {
        backdrop: 'static',
        keyboard: false
    });

    document.getElementById('openSummaryModalBtn').addEventListener('click', function() {
        summaryModal.show();
    });
});
