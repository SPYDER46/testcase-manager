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

    // === Add Test Suite form submit handler ===
    const testSuiteForm = document.getElementById('testSuiteForm');
    if (testSuiteForm) {
        testSuiteForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const testCaseId = document.getElementById('hiddenTestcaseId').value;
            const suiteName = document.getElementById('suiteName').value.trim();
            const suiteDescription = document.getElementById('suiteDescription').value.trim();

            if (!suiteName) {
                alert('Test Suite Name is required.');
                return;
            }

            fetch('/add_test_suite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    test_case_id: testCaseId,
                    suite_name: suiteName,
                    description: suiteDescription
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Test Suite added successfully.');
                    const modalEl = document.getElementById('testSuiteModal');
                    const modalInstance = bootstrap.Modal.getInstance(modalEl);
                    modalInstance.hide();
                    location.reload();
                } else {
                    alert('Failed to add test suite.');
                }
            })
            .catch(() => alert('Error adding test suite.'));
        });
    }

});
