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
