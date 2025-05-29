document.addEventListener('DOMContentLoaded', function () {
    // === Delete Confirmation Modal ===
    const deleteConfirmModalEl = document.getElementById('deleteConfirmModal');
    const deleteConfirmForm = document.getElementById('deleteConfirmForm');
    const deleteConfirmModal = deleteConfirmModalEl ? new bootstrap.Modal(deleteConfirmModalEl, {
        backdrop: 'static',
        keyboard: false
    }) : null;

    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function () {
            const deleteUrl = this.getAttribute('data-url');
            if (deleteUrl && deleteConfirmForm) {
                deleteConfirmForm.action = deleteUrl;
                deleteConfirmModal.show();
            }
        });
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

                // Add image to PDF at fixed position and width (auto height)
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
});
