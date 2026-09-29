/* -------------------------------------------------------------
 * CYBERVAULT CLIENT-SIDE WEB-CRYPTO ENGINE & CONTROLLER
 * ------------------------------------------------------------- */

// Global State
let derivedKey = null;
let currentSalt = null;
let vaultRecords = [];
let clipboardTimerId = null;
let clipboardSecondsLeft = 0;

const STORAGE_KEY_VAULT = "cybervault_encrypted_vault";
const STORAGE_KEY_CONFIG = "cybervault_config";

const AMBIGUOUS_CHARS = "l1IO0o";
const SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?";

// -------------------------------------------------------------
// 1. WEB CRYPTO HELPER FUNCTIONS (AES-GCM + PBKDF2)
// -------------------------------------------------------------
function bufferToBase64(buffer) {
    return btoa(String.fromCharCode(...new Uint8Array(buffer)));
}

function base64ToBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
}

async function deriveMasterKey(password, saltUint8Array) {
    const enc = new TextEncoder();
    const keyMaterial = await window.crypto.subtle.importKey(
        "raw",
        enc.encode(password),
        "PBKDF2",
        false,
        ["deriveKey"]
    );

    return await window.crypto.subtle.deriveKey(
        {
            name: "PBKDF2",
            salt: saltUint8Array,
            iterations: 200000,
            hash: "SHA-256"
        },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        false,
        ["encrypt", "decrypt"]
    );
}

async function encryptData(plaintext, key) {
    if (!plaintext) return "";
    const enc = new TextEncoder();
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await window.crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        key,
        enc.encode(plaintext)
    );
    return JSON.stringify({
        iv: bufferToBase64(iv),
        ct: bufferToBase64(ciphertext)
    });
}

async function decryptData(encryptedJsonStr, key) {
    if (!encryptedJsonStr) return "";
    try {
        const dec = new TextDecoder();
        const { iv, ct } = JSON.parse(encryptedJsonStr);
        const decrypted = await window.crypto.subtle.decrypt(
            { name: "AES-GCM", iv: new Uint8Array(base64ToBuffer(iv)) },
            key,
            base64ToBuffer(ct)
        );
        return dec.decode(decrypted);
    } catch (e) {
        return "[DECRYPTION_ERROR]";
    }
}

// -------------------------------------------------------------
// 2. CSPRNG PASSWORD GENERATOR & ENTROPY
// -------------------------------------------------------------
function getRandomInt(max) {
    const array = new Uint32Array(1);
    window.crypto.getRandomValues(array);
    return array[0] % max;
}

function generatePassword(length = 18, useUpper = true, useLower = true, useDigits = true, useSymbols = true, excludeAmbiguous = false) {
    let upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    let lower = "abcdefghijklmnopqrstuvwxyz";
    let digits = "0123456789";
    let symbols = SPECIAL_CHARS;

    if (excludeAmbiguous) {
        upper = [...upper].filter(c => !AMBIGUOUS_CHARS.includes(c)).join('');
        lower = [...lower].filter(c => !AMBIGUOUS_CHARS.includes(c)).join('');
        digits = [...digits].filter(c => !AMBIGUOUS_CHARS.includes(c)).join('');
        symbols = [...symbols].filter(c => !AMBIGUOUS_CHARS.includes(c)).join('');
    }

    const pools = [];
    const guaranteed = [];

    if (useUpper && upper) { pools.push(upper); guaranteed.push(upper[getRandomInt(upper.length)]); }
    if (useLower && lower) { pools.push(lower); guaranteed.push(lower[getRandomInt(lower.length)]); }
    if (useDigits && digits) { pools.push(digits); guaranteed.push(digits[getRandomInt(digits.length)]); }
    if (useSymbols && symbols) { pools.push(symbols); guaranteed.push(symbols[getRandomInt(symbols.length)]); }

    if (pools.length === 0) {
        pools.push(lower + digits);
        guaranteed.push(lower[getRandomInt(lower.length)]);
    }

    const combinedPool = pools.join('');
    const remainingLen = Math.max(0, length - guaranteed.length);
    const randomChars = [];

    for (let i = 0; i < remainingLen; i++) {
        randomChars.push(combinedPool[getRandomInt(combinedPool.length)]);
    }

    const passwordList = [...guaranteed, ...randomChars];
    // Fisher-Yates CSPRNG shuffle
    for (let i = passwordList.length - 1; i > 0; i--) {
        const j = getRandomInt(i + 1);
        [passwordList[i], passwordList[j]] = [passwordList[j], passwordList[i]];
    }

    return passwordList.join('');
}

function calculateEntropy(password) {
    if (!password) return 0;
    let poolSize = 0;
    if (/[a-z]/.test(password)) poolSize += 26;
    if (/[A-Z]/.test(password)) poolSize += 26;
    if (/[0-9]/.test(password)) poolSize += 10;
    if (/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) poolSize += SPECIAL_CHARS.length;
    if (/[^a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) poolSize += 30;

    if (poolSize === 0) return 0;
    return Math.round(password.length * Math.log2(poolSize) * 10) / 10;
}

function evaluateStrength(password) {
    const entropy = calculateEntropy(password);
    if (entropy < 35) return { label: "WEAK", entropy, color: "#ff2a6d" };
    if (entropy < 60) return { label: "MEDIUM", entropy, color: "#ffb800" };
    if (entropy < 90) return { label: "STRONG", entropy, color: "#00f0ff" };
    return { label: "OVERKILL", entropy, color: "#00ff66" };
}

// -------------------------------------------------------------
// 3. AUTHENTICATION & VAULT INITIALIZATION
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    checkVaultInitialization();
    generateNewPassword();
});

function checkVaultInitialization() {
    const configStr = localStorage.getItem(STORAGE_KEY_CONFIG);
    const badge = document.getElementById("auth-badge");
    const label = document.getElementById("auth-label");
    const confirmGroup = document.getElementById("confirm-pass-group");
    const submitBtn = document.getElementById("auth-submit-btn");

    if (!configStr) {
        badge.textContent = "● INITIAL SETUP: CREATE MASTER KEY";
        badge.className = "badge badge-amber";
        label.textContent = "CREATE MASTER PASSWORD:";
        confirmGroup.classList.remove("hidden");
        submitBtn.innerHTML = '<span class="btn-glitch"></span>INITIALIZE VAULT';
    } else {
        badge.textContent = "● AUTHENTICATION REQUIRED";
        badge.className = "badge badge-green";
        label.textContent = "ENTER MASTER PASSWORD:";
        confirmGroup.classList.add("hidden");
        submitBtn.innerHTML = '<span class="btn-glitch"></span>UNLOCK VAULT';
    }
}

async function handleAuthSubmit(event) {
    event.preventDefault();
    const pass = document.getElementById("master-password-input").value;
    const confirmPass = document.getElementById("confirm-password-input").value;
    const configStr = localStorage.getItem(STORAGE_KEY_CONFIG);

    if (!configStr) {
        if (pass !== confirmPass) {
            alert("Passwords do not match!");
            return;
        }
        if (pass.length < 6) {
            alert("Master password must be at least 6 characters.");
            return;
        }
        const salt = window.crypto.getRandomValues(new Uint8Array(16));
        derivedKey = await deriveMasterKey(pass, salt);
        currentSalt = salt;

        // Create Canary
        const canary = await encryptData("CYBERVAULT_CANARY_OK", derivedKey);

        const config = {
            salt: bufferToBase64(salt),
            canary: canary
        };
        localStorage.setItem(STORAGE_KEY_CONFIG, JSON.stringify(config));
        unlockVaultUI();
    } else {
        const config = JSON.parse(configStr);
        const salt = new Uint8Array(base64ToBuffer(config.salt));
        const candidateKey = await deriveMasterKey(pass, salt);

        const decryptedCanary = await decryptData(config.canary, candidateKey);
        if (decryptedCanary === "CYBERVAULT_CANARY_OK") {
            derivedKey = candidateKey;
            currentSalt = salt;
            unlockVaultUI();
        } else {
            alert("Access Denied: Invalid Master Password.");
            document.getElementById("master-password-input").value = "";
        }
    }
}

async function unlockVaultUI() {
    document.getElementById("auth-gateway").classList.add("hidden");
    document.getElementById("app-container").classList.remove("hidden");
    await loadVaultFromStorage();
    runAuditScan();
}

function lockVault() {
    derivedKey = null;
    currentSalt = null;
    vaultRecords = [];
    document.getElementById("app-container").classList.add("hidden");
    document.getElementById("auth-gateway").classList.remove("hidden");
    document.getElementById("master-password-input").value = "";
    document.getElementById("confirm-password-input").value = "";
}

// -------------------------------------------------------------
// 4. VAULT RECORD MANAGMENT (ENCRYPTED CRUD)
// -------------------------------------------------------------
async function loadVaultFromStorage() {
    const raw = localStorage.getItem(STORAGE_KEY_VAULT);
    vaultRecords = [];
    if (raw) {
        try {
            const encryptedList = JSON.parse(raw);
            for (const item of encryptedList) {
                const website = await decryptData(item.website, derivedKey);
                const username = await decryptData(item.username, derivedKey);
                const password = await decryptData(item.password, derivedKey);
                const category = await decryptData(item.category, derivedKey) || "General";
                const notes = await decryptData(item.notes, derivedKey) || "";

                vaultRecords.push({
                    id: item.id,
                    website,
                    username,
                    password,
                    category,
                    notes,
                    updated_at: item.updated_at
                });
            }
        } catch (e) {
            console.error("Failed to decrypt vault records", e);
        }
    }
    renderVaultTable(vaultRecords);
}

async function saveVaultToStorage() {
    const encryptedList = [];
    for (const rec of vaultRecords) {
        encryptedList.push({
            id: rec.id,
            website: await encryptData(rec.website, derivedKey),
            username: await encryptData(rec.username, derivedKey),
            password: await encryptData(rec.password, derivedKey),
            category: await encryptData(rec.category, derivedKey),
            notes: await encryptData(rec.notes, derivedKey),
            updated_at: rec.updated_at
        });
    }
    localStorage.setItem(STORAGE_KEY_VAULT, JSON.stringify(encryptedList));
}

function renderVaultTable(records) {
    const tbody = document.getElementById("vault-tbody");
    tbody.innerHTML = "";

    if (records.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-muted);">Vault is empty. Click '+ ADD CREDENTIAL' to begin.</td></tr>`;
        return;
    }

    records.forEach(rec => {
        const { label, entropy, color } = evaluateStrength(rec.password);
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>${rec.id}</td>
            <td><strong>${escapeHtml(rec.website)}</strong></td>
            <td>${escapeHtml(rec.username)}</td>
            <td><span class="badge" style="background: rgba(0,240,255,0.1); color: var(--cyan);">${escapeHtml(rec.category)}</span></td>
            <td><span style="color: ${color}; font-weight: bold;">${label} (${Math.round(entropy)}b)</span></td>
            <td>${rec.updated_at}</td>
            <td>
                <button class="cyber-button btn-blue btn-sm" onclick="copyUsername('${rec.id}')">📋 USER</button>
                <button class="cyber-button btn-cyan btn-sm" onclick="copyPassword('${rec.id}')">🔑 PASS</button>
                <button class="cyber-button btn-amber btn-sm" onclick="openEditModal('${rec.id}')">✏️ EDIT</button>
                <button class="cyber-button btn-red btn-sm" onclick="deleteCredential('${rec.id}')">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterVault() {
    const query = document.getElementById("search-input").value.toLowerCase();
    const filtered = vaultRecords.filter(r => 
        r.website.toLowerCase().includes(query) ||
        r.username.toLowerCase().includes(query) ||
        r.category.toLowerCase().includes(query)
    );
    renderVaultTable(filtered);
}

function openAddModal() {
    document.getElementById("modal-title").textContent = "ADD NEW CREDENTIAL";
    document.getElementById("edit-id").value = "";
    document.getElementById("cred-form").reset();
    document.getElementById("cred-modal").classList.remove("hidden");
}

function openEditModal(id) {
    const rec = vaultRecords.find(r => String(r.id) === String(id));
    if (!rec) return;

    document.getElementById("modal-title").textContent = "EDIT CREDENTIAL";
    document.getElementById("edit-id").value = rec.id;
    document.getElementById("cred-website").value = rec.website;
    document.getElementById("cred-username").value = rec.username;
    document.getElementById("cred-password").value = rec.password;
    document.getElementById("cred-category").value = rec.category || "General";
    document.getElementById("cred-notes").value = rec.notes || "";
    document.getElementById("cred-modal").classList.remove("hidden");
}

function closeCredModal() {
    document.getElementById("cred-modal").classList.add("hidden");
}

async function saveCredential(event) {
    event.preventDefault();
    const editId = document.getElementById("edit-id").value;
    const website = document.getElementById("cred-website").value.trim();
    const username = document.getElementById("cred-username").value.trim();
    const password = document.getElementById("cred-password").value.trim();
    const category = document.getElementById("cred-category").value;
    const notes = document.getElementById("cred-notes").value.trim();
    const now = new Date().toISOString().split('T')[0];

    if (editId) {
        const index = vaultRecords.findIndex(r => String(r.id) === String(editId));
        if (index !== -1) {
            vaultRecords[index] = { id: parseInt(editId), website, username, password, category, notes, updated_at: now };
        }
    } else {
        const newId = vaultRecords.length > 0 ? Math.max(...vaultRecords.map(r => r.id)) + 1 : 1;
        vaultRecords.push({ id: newId, website, username, password, category, notes, updated_at: now });
    }

    await saveVaultToStorage();
    renderVaultTable(vaultRecords);
    closeCredModal();
    runAuditScan();
}

async function deleteCredential(id) {
    if (confirm("Are you sure you want to delete this credential?")) {
        vaultRecords = vaultRecords.filter(r => String(r.id) !== String(id));
        await saveVaultToStorage();
        renderVaultTable(vaultRecords);
        runAuditScan();
    }
}

// -------------------------------------------------------------
// 5. CLIPBOARD & GENERATOR CONTROLLERS
// -------------------------------------------------------------
function generateNewPassword() {
    const len = parseInt(document.getElementById("length-slider").value);
    const useUpper = document.getElementById("cb-upper").checked;
    const useLower = document.getElementById("cb-lower").checked;
    const useDigits = document.getElementById("cb-digits").checked;
    const useSymbols = document.getElementById("cb-symbols").checked;
    const excludeAmbiguous = document.getElementById("cb-ambiguous").checked;

    const pass = generatePassword(len, useUpper, useLower, useDigits, useSymbols, excludeAmbiguous);
    document.getElementById("gen-output").value = pass;

    const { label, entropy, color } = evaluateStrength(pass);
    const fillPercent = Math.min(100, Math.round((entropy / 100) * 100));

    const fillElem = document.getElementById("meter-fill");
    fillElem.style.width = `${fillPercent}%`;
    fillElem.style.backgroundColor = color;

    const labelElem = document.getElementById("strength-label");
    labelElem.textContent = `SECURITY LEVEL: ${label} (${entropy} bits entropy)`;
    labelElem.style.color = color;
}

function onLengthChange(val) {
    document.getElementById("length-val").textContent = val;
    generateNewPassword();
}

function copyGenPassword() {
    const pwd = document.getElementById("gen-output").value;
    if (pwd) {
        copyToClipboard(pwd, "Password");
    }
}

function copyUsername(id) {
    const rec = vaultRecords.find(r => String(r.id) === String(id));
    if (rec) copyToClipboard(rec.username, `Username '${rec.username}'`);
}

function copyPassword(id) {
    const rec = vaultRecords.find(r => String(r.id) === String(id));
    if (rec) copyToClipboard(rec.password, "Password");
}

function copyToClipboard(text, label) {
    navigator.clipboard.writeText(text).then(() => {
        alert(`${label} copied to clipboard!`);
        startClipboardTimer(30);
    });
}

function startClipboardTimer(seconds) {
    if (clipboardTimerId) clearInterval(clipboardTimerId);
    clipboardSecondsLeft = seconds;
    updateClipboardTimerUI();

    clipboardTimerId = setInterval(() => {
        clipboardSecondsLeft--;
        updateClipboardTimerUI();
        if (clipboardSecondsLeft <= 0) {
            clearInterval(clipboardTimerId);
            navigator.clipboard.writeText("");
            document.getElementById("clipboard-timer").textContent = "📋 CLIPBOARD CLEARED";
        }
    }, 1000);
}

function updateClipboardTimerUI() {
    if (clipboardSecondsLeft > 0) {
        document.getElementById("clipboard-timer").textContent = `📋 CLIPBOARD CLEARS IN ${clipboardSecondsLeft}s`;
    }
}

// -------------------------------------------------------------
// 6. SECURITY AUDIT DASHBOARD
// -------------------------------------------------------------
function runAuditScan() {
    const total = vaultRecords.length;
    let weakCount = 0;
    const passCounts = {};
    const weakList = [];

    vaultRecords.forEach(r => {
        const { entropy } = evaluateStrength(r.password);
        if (entropy < 50) {
            weakCount++;
            weakList.push(`${r.website} (${r.username}) - ${entropy}b`);
        }
        passCounts[r.password] = (passCounts[r.password] || 0) + 1;
    });

    let reusedCount = 0;
    Object.values(passCounts).forEach(c => { if (c > 1) reusedCount += c; });

    const score = Math.max(0, 100 - (weakCount * 15 + reusedCount * 10));

    document.getElementById("metric-total").textContent = total;
    document.getElementById("metric-weak").textContent = weakCount;
    document.getElementById("metric-reused").textContent = reusedCount;
    document.getElementById("metric-score").textContent = `${score}%`;

    const reportLines = [
        "==========================================================================",
        "              CYBERVAULT WEB VULNERABILITY AUDIT REPORT                   ",
        "==========================================================================",
        `[+] Total Accounts Scanned: ${total}`,
        `[+] Security Health Score: ${score}%`,
        `[+] Cryptographic Engine: Web Crypto API (AES-GCM-256 + PBKDF2-SHA256)`,
        "--------------------------------------------------------------------------\n"
    ];

    if (weakList.length > 0) {
        reportLines.push("[!] WEAK PASSWORDS DETECTED (Low Entropy < 50 bits):");
        weakList.forEach(w => reportLines.push(`    - ${w}`));
        reportLines.push("");
    }

    if (reusedCount > 0) {
        reportLines.push("[!] REUSED PASSWORDS DETECTED across multiple accounts!");
        reportLines.push("");
    }

    if (weakList.length === 0 && reusedCount === 0) {
        reportLines.push("[✓] EXCELLENT SECURITY POSTURE! Zero weak or reused passwords detected.");
    }

    document.getElementById("audit-report").value = reportLines.join("\n");
}

// -------------------------------------------------------------
// 7. BACKUP / RESTORE (.CYBERVAULT & CSV)
// -------------------------------------------------------------
async function exportEncryptedBackup() {
    const pass = prompt("Enter a backup encryption password:");
    if (!pass) return;

    const salt = window.crypto.getRandomValues(new Uint8Array(16));
    const backupKey = await deriveMasterKey(pass, salt);

    const rawJson = JSON.stringify(vaultRecords);
    const encryptedPayload = await encryptData(rawJson, backupKey);

    const bundle = {
        version: "2.0.0-web",
        salt: bufferToBase64(salt),
        payload: encryptedPayload
    };

    downloadFile(JSON.stringify(bundle, null, 4), "cybervault_backup.cybervault", "application/json");
}

function importEncryptedBackup() {
    const input = document.getElementById("file-input");
    input.accept = ".json,.cybervault";
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const text = await file.text();
        const bundle = JSON.parse(text);

        const pass = prompt("Enter the backup password used to encrypt this file:");
        if (!pass) return;

        try {
            const salt = new Uint8Array(base64ToBuffer(bundle.salt));
            const backupKey = await deriveMasterKey(pass, salt);
            const decryptedJson = await decryptData(bundle.payload, backupKey);
            const imported = JSON.parse(decryptedJson);

            let count = 0;
            for (const item of imported) {
                if (item.website && item.username && item.password) {
                    const newId = vaultRecords.length > 0 ? Math.max(...vaultRecords.map(r => r.id)) + 1 : 1;
                    vaultRecords.push({
                        id: newId,
                        website: item.website,
                        username: item.username,
                        password: item.password,
                        category: item.category || "Imported",
                        notes: item.notes || "",
                        updated_at: new Date().toISOString().split('T')[0]
                    });
                    count++;
                }
            }
            await saveVaultToStorage();
            renderVaultTable(vaultRecords);
            runAuditScan();
            alert(`Successfully imported ${count} credentials into vault!`);
        } catch (err) {
            alert("Failed to decrypt backup file. Invalid password or corrupted bundle.");
        }
    };
    input.click();
}

function exportCSV() {
    if (!confirm("Warning: Plain CSV files store passwords unencrypted! Continue?")) return;
    let csv = "Website,Username,Password,Category,Notes\n";
    vaultRecords.forEach(r => {
        csv += `"${r.website}","${r.username}","${r.password}","${r.category}","${r.notes}"\n`;
    });
    downloadFile(csv, "cybervault_passwords.csv", "text/csv");
}

function importCSV() {
    const input = document.getElementById("file-input");
    input.accept = ".csv";
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const text = await file.text();
        const lines = text.split("\n");
        let count = 0;
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;
            const cols = line.split(",").map(c => c.replace(/^"|"$/g, '').trim());
            if (cols.length >= 3 && cols[0] && cols[1] && cols[2]) {
                const newId = vaultRecords.length > 0 ? Math.max(...vaultRecords.map(r => r.id)) + 1 : 1;
                vaultRecords.push({
                    id: newId,
                    website: cols[0],
                    username: cols[1],
                    password: cols[2],
                    category: cols[3] || "General",
                    notes: cols[4] || "",
                    updated_at: new Date().toISOString().split('T')[0]
                });
                count++;
            }
        }
        await saveVaultToStorage();
        renderVaultTable(vaultRecords);
        runAuditScan();
        alert(`Imported ${count} records from CSV.`);
    };
    input.click();
}

// Helper Functions
function switchTab(tabId, btn) {
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.getElementById(tabId).classList.add("active");
    btn.classList.add("active");
}

function toggleAuthEye() {
    const inp = document.getElementById("master-password-input");
    inp.type = inp.type === "password" ? "text" : "password";
}

function toggleCredEye() {
    const inp = document.getElementById("cred-password");
    inp.type = inp.type === "password" ? "text" : "password";
}

function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
}

function escapeHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
