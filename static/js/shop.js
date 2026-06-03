

        function switchShop(shopkeeperId) {
            window.location.href = `/shop?shopkeeper_id=${shopkeeperId}`;
        }

        function downloadTemplate() {
            window.location.href = `/api/inventory/template/${ACTIVE_SHOPKEEPER_ID}`;
        }

        async function uploadCsv() {
            const fileInput = document.getElementById('csv-file');

            if (fileInput.files.length === 0) {
                alert('Please select a CSV file to upload.');
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
                    alert(data.detail || 'Inventory updated successfully!');
                    location.reload();
                } else {
                    alert(data.detail || 'Failed to upload CSV.');
                }
            } catch (err) {
                alert('Error uploading CSV.');
            }
        }
    