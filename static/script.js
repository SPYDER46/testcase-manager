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
                    deleteConfirmMessage.textContent = "Are you sure you want to delete this Test Case? This action cannot be undone.";
                } else if (itemType === 'iteration') {
                    deleteConfirmMessage.textContent = "Are you sure you want to delete this iteration? This action cannot be undone.";
                } else if (itemType === 'testcase') {
                    deleteConfirmMessage.textContent = "Are you sure you want to delete this Test suite? This action cannot be undone.";
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

});
