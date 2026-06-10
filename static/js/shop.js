
// Added for XSS protection
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return str.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}



        function switchShop(shopkeeperId) {
            window.location.href = `/shop?shopkeeper_id=${shopkeeperId}`;
        }

        function downloadTemplate() {
            window.location.href = `/api/inventory/template/${ACTIVE_SHOPKEEPER_ID}`;
        }

        async function uploadCsv() {
            const fileInput = document.getElementById('csv-file');

            if (fileInput.files.length === 0) {
                await Swal.fire('Please select a CSV file to upload.');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('shopkeeper_id', ACTIVE_SHOPKEEPER_ID);

            try {
                const response = await fetch('/api/inventory/bulk_upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (response.ok) {
                    await Swal.fire(data.detail || 'Inventory updated successfully!');
                    location.reload();
                } else {
                    await Swal.fire(data.detail || 'Failed to upload CSV.');
                }
            } catch (err) {
                await Swal.fire('Error uploading CSV.');
            }
        }
    