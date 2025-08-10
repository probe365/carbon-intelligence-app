// 🔄 Alternância de idioma
function toggleLanguage() {
    const en = document.getElementById("english");
    const pt = document.getElementById("portuguese");

    if (en.style.display === "none") {
        en.style.display = "block";
        pt.style.display = "none";
    } else {
        en.style.display = "none";
        pt.style.display = "block";
    }
}

// 🔐 Salvar trial_key como cookie
function setTrialKeyCookie(trialKey) {
    document.cookie = `trial_key=${trialKey}; path=/; max-age=86400`;
}

// 🔍 Recuperar trial_key do cookie
function getTrialKeyFromCookie() {
    const match = document.cookie.match(/(^|;)\\s*trial_key=([^;]+)/);
    return match ? match[2] : null;
}

// 📤 Enviar requisição de busca
async function buscarInteligenciaDeCarbono(query) {
    const trialKey = getTrialKeyFromCookie();

    const response = await fetch('/api/busca', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, trial_key: trialKey })
    });

    const data = await response.json();

    if (data.error) {
        alert("Erro: " + data.error);
    } else {
        console.log("Resultado:", data.resultado);
        // Aqui você pode atualizar o DOM com o resultado
    }
}

