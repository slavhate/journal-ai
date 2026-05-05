document.addEventListener("DOMContentLoaded", () => {
    const datePicker = document.getElementById("date-picker");
    const entryInput = document.getElementById("entry-input");
    const submitBtn = document.getElementById("submit-btn");
    const entriesList = document.getElementById("entries-list");
    const eventsList = document.getElementById("events-list");

    const today = new Date().toISOString().split("T")[0];
    datePicker.value = today;

    function getSelectedCategory() {
        return document.querySelector('input[name="category"]:checked').value;
    }

    async function submitEntry() {
        const text = entryInput.value.trim();
        if (!text) return;

        submitBtn.disabled = true;
        submitBtn.textContent = "Saving...";

        try {
            const response = await fetch("/api/entries", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ category: getSelectedCategory(), raw_text: text })
            });

            if (response.ok) {
                entryInput.value = "";
                await loadEntries(today);
                await loadEvents();
            } else {
                showError("Failed to save entry. Please try again.");
            }
        } catch {
            showError("Network error. Check your connection.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Submit";
        }
    }

    submitBtn.addEventListener("click", submitEntry);
    entryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") submitEntry();
    });

    async function loadEntries(date) {
        try {
            const response = await fetch(`/api/entries/${date}`);
            if (!response.ok) {
                entriesList.innerHTML = '<p class="empty-state">No entries yet</p>';
                return;
            }
            const data = await response.json();
            renderEntries(data, date === today);
        } catch {
            entriesList.innerHTML = '<p class="empty-state">Could not load entries</p>';
        }
    }

    function renderMarkdown(md) {
        return md
            .split("\n")
            .map(line => {
                if (line.startsWith("### ")) return `<h4>${escapeHtml(line.slice(4))}</h4>`;
                if (line.startsWith("- ")) return `<li>${escapeHtml(line.slice(2))}</li>`;
                return "";
            })
            .join("")
            .replace(/(<li>.*<\/li>)+/g, match => `<ul>${match}</ul>`);
    }

    function renderEntries(grouped, editable) {
        const categories = ["work", "personal", "finance"];
        const labels = { work: "Work", personal: "Personal", finance: "Finance" };
        let html = "";

        for (const cat of categories) {
            const entries = grouped[cat] || [];
            if (entries.length === 0) continue;

            html += `<div class="category-group"><h3>${labels[cat]}</h3>`;
            for (const entry of entries) {
                const safeId = parseInt(entry.id, 10);
                html += `<div class="entry-item" data-id="${safeId}" data-raw-text="${escapeAttr(entry.raw_text)}">`;
                html += `<div class="entry-text">${renderMarkdown(entry.formatted_md || entry.raw_text)}</div>`;
                if (editable) {
                    html += `<div class="entry-actions">`;
                    html += `<button class="btn-edit" data-id="${safeId}">&#9998;</button>`;
                    html += `<button class="btn-delete" data-id="${safeId}">&#10005;</button>`;
                    html += `</div>`;
                }
                html += `</div>`;
            }
            html += `</div>`;
        }

        if (!html) {
            html = '<p class="empty-state">No entries yet</p>';
        }

        entriesList.innerHTML = html;
    }

    entriesList.addEventListener("click", (e) => {
        const editBtn = e.target.closest(".btn-edit");
        const deleteBtn = e.target.closest(".btn-delete");
        if (editBtn) {
            const id = parseInt(editBtn.dataset.id, 10);
            if (!isNaN(id)) editEntry(id, editBtn);
        } else if (deleteBtn) {
            const id = parseInt(deleteBtn.dataset.id, 10);
            if (!isNaN(id)) deleteEntry(id);
        }
    });

    async function loadEvents() {
        try {
            const response = await fetch("/api/todos");
            if (!response.ok) return;
            const todos = await response.json();

            if (todos.length === 0) {
                eventsList.innerHTML = '<p class="empty-state">No upcoming todos</p>';
                return;
            }

            const todayStr = today;
            let html = "";
            for (const todo of todos) {
                const isToday = todo.date === todayStr;
                const label = isToday ? "Today" : todo.date;
                html += `<div class="event-item">
                    <span class="event-icon">&#9744;</span>
                    <div class="event-body">
                        <span class="event-title">${escapeHtml(todo.title)}</span>
                        <span class="event-date${isToday ? " event-date--today" : ""}">${label}</span>
                    </div>
                </div>`;
            }
            eventsList.innerHTML = html;
        } catch {
            eventsList.innerHTML = '<p class="empty-state">Could not load todos</p>';
        }
    }

    datePicker.addEventListener("change", () => {
        const date = datePicker.value;
        const isToday = date === today;

        const formSection = document.querySelector(".entry-form");
        const heading = document.querySelector(".entries-section h2");

        if (isToday) {
            formSection.style.display = "";
            heading.textContent = "Today's Entries";
            const notice = document.querySelector(".read-only-notice");
            if (notice) notice.remove();
        } else {
            formSection.style.display = "none";
            heading.textContent = `Entries for ${date}`;
            if (!document.querySelector(".read-only-notice")) {
                const notice = document.createElement("div");
                notice.className = "read-only-notice";
                notice.textContent = "Viewing past entries (read-only)";
                document.querySelector(".entries-section").prepend(notice);
            }
        }

        loadEntries(date);
    });

    function editEntry(id, btn) {
        const item = btn.closest(".entry-item");
        const currentText = item.dataset.rawText || item.querySelector(".entry-text")?.textContent || "";
        item.innerHTML = `
            <div class="edit-form">
                <input type="text" value="${escapeAttr(currentText)}" class="edit-input" data-id="${id}">
                <button class="save-btn" data-id="${id}">Save</button>
                <button class="cancel-btn">Cancel</button>
            </div>
        `;
        item.querySelector(".edit-input").focus();
        item.querySelector(".save-btn").addEventListener("click", () => saveEdit(id, item));
        item.querySelector(".cancel-btn").addEventListener("click", () => loadEntries(today));
    }

    async function saveEdit(id, item) {
        const input = item.querySelector(".edit-input");
        const newText = input.value.trim();
        if (!newText) return;

        try {
            const response = await fetch(`/api/entries/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ raw_text: newText })
            });

            if (response.ok) {
                await loadEntries(today);
            } else {
                showError("Failed to update entry.");
            }
        } catch {
            showError("Network error. Could not update entry.");
        }
    }

    async function deleteEntry(id) {
        try {
            const response = await fetch(`/api/entries/${id}`, { method: "DELETE" });
            if (response.ok) {
                await loadEntries(today);
            } else {
                showError("Failed to delete entry.");
            }
        } catch {
            showError("Network error. Could not delete entry.");
        }
    }

    function showError(message) {
        const existing = document.getElementById("error-toast");
        if (existing) existing.remove();
        const toast = document.createElement("div");
        toast.id = "error-toast";
        toast.className = "error-toast";
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeAttr(text) {
        return text.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    async function checkAiStatus() {
        const el = document.getElementById("ai-status");
        const dot = el.querySelector(".ai-status__dot");
        const label = el.querySelector(".ai-status__label");
        try {
            const resp = await fetch("/api/health");
            const data = await resp.json();
            el.className = `ai-status ai-status--${data.status}`;
            if (data.status === "ready") {
                label.textContent = "AI Ready";
                label.title = `${data.formatting_model.name} · ${data.embedding_model.name}`;
            } else if (data.status === "partial") {
                const missing = [
                    !data.formatting_model.available && data.formatting_model.name,
                    !data.embedding_model.available && data.embedding_model.name,
                ].filter(Boolean).join(", ");
                label.textContent = "AI Partial";
                label.title = `Missing models: ${missing}`;
            } else {
                label.textContent = "AI Offline";
                label.title = "Ollama is not reachable";
            }
        } catch {
            el.className = "ai-status ai-status--offline";
            label.textContent = "AI Offline";
        }
    }

    checkAiStatus();
    setInterval(checkAiStatus, 30000);

    loadEntries(today);
    loadEvents();
});
