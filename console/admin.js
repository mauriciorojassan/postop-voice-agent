document.addEventListener("DOMContentLoaded", () => {
    loadDocuments();

    const uploadForm = document.getElementById("uploadForm");
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById("pdfFile");
        const statusDiv = document.getElementById("uploadStatus");

        if (fileInput.files.length === 0) return;

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        statusDiv.textContent = "Subiendo e indexando...";
        statusDiv.className = "mt-2 text-sm text-blue-600";

        try {
            const response = await fetch("/api/documents", {
                method: "POST",
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                statusDiv.textContent = `¡Éxito! Documento indexado: ${result.title} (${result.chunks} fragmentos)`;
                statusDiv.className = "mt-2 text-sm text-green-600";
                fileInput.value = "";
                loadDocuments();
            } else {
                const err = await response.json();
                statusDiv.textContent = `Error: ${err.detail || 'Fallo en la subida'}`;
                statusDiv.className = "mt-2 text-sm text-red-600";
            }
        } catch (error) {
            statusDiv.textContent = `Error de red: ${error.message}`;
            statusDiv.className = "mt-2 text-sm text-red-600";
        }
    });
});

async function loadDocuments() {
    try {
        const response = await fetch("/api/documents");
        if (!response.ok) return;
        const docs = await response.json();
        const tbody = document.getElementById("docsTableBody");
        tbody.innerHTML = "";

        if (docs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="py-4 px-6 text-center text-gray-400">No hay documentos cargados.</td></tr>`;
            return;
        }

        docs.forEach(doc => {
            let badgeClass = "bg-yellow-200 text-yellow-800";
            if (doc.status === "Processed and Available") {
                badgeClass = "bg-green-200 text-green-800";
            } else if (doc.status === "Error") {
                badgeClass = "bg-red-200 text-red-800";
            }

            const tr = document.createElement("tr");
            tr.className = "border-b border-gray-200 hover:bg-gray-100";
            tr.innerHTML = `
                <td class="py-3 px-6 text-left whitespace-nowrap font-medium">${doc.title}</td>
                <td class="py-3 px-6 text-center">
                    <span class="py-1 px-3 rounded-full text-xs font-semibold ${badgeClass}">${doc.status}</span>
                </td>
                <td class="py-3 px-6 text-center">${doc.chunks}</td>
                <td class="py-3 px-6 text-center">${doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleString() : '-'}</td>
                <td class="py-3 px-6 text-center">
                    <button onclick="deleteDocument('${doc.doc_id}')" class="bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-600">Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error("Error loading documents:", error);
    }
}

async function deleteDocument(docId) {
    if (!confirm(`¿Eliminar documento ${docId} y purgar sus vectores de ChromaDB?`)) return;

    try {
        const response = await fetch(`/api/documents/${encodeURIComponent(docId)}`, {
            method: "DELETE"
        });

        if (response.ok) {
            loadDocuments();
        } else {
            alert("Error al eliminar el documento.");
        }
    } catch (error) {
        console.error("Error deleting document:", error);
    }
}
