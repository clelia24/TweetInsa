// Récupération des éléments HTML
const modal = document.getElementById("tweetModal");
const openBtn = document.getElementById("openModalBtn");
const closeBtn = document.getElementsByClassName("close")[0];

// Ouvrir la modale quand on clique sur "Publier"
openBtn.onclick = function() {
    modal.style.display = "block";
}

// Fermer la modale quand on clique sur le X
closeBtn.onclick = function() {
    modal.style.display = "none";
}

// Fermer la modale quand on clique en dehors du contenu
window.onclick = function(event) {
    if (event.target === modal) {
        modal.style.display = "none";
    }
}
