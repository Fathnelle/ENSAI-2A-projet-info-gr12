from InquirerPy import inquirer

from view.vue_abstraite import VueAbstraite
from view.session import Session

# from view.menu_administrateur_vue import MenuAdministrateurVue
from view.menu_utilisateur_vue import MenuUtilisateurVue

from service.utilisateur_service import UtilisateurService


class ConnexionVue(VueAbstraite):
    """Vue de Connexion (saisie de pseudo et mdp)"""

    def __init__(self, message=""):
        self.message = message

    def choisir_menu(self):
        # Demande à l'utilisateur de saisir pseudo et mot de passe
        pseudo = inquirer.text(message="Entrez votre pseudo : ").execute()
        mdp = inquirer.secret(message="Entrez votre mot de passe :").execute()

        # Appel du service pour trouver l'utilisateur
        user = UtilisateurService().seConnecter(pseudo, mdp)

        # Si l'utilisateur a été trouvé à partir des ses identifiants de connexion
        if user:
            print(f"\nVous êtes connecté sous le pseudo {user.pseudo}\n")
            Session().connexion(user)
            return MenuUtilisateurVue()
        else:
            print("\nErreur de connexion (pseudo ou mot de passe invalide)\n")
            return ConnexionVue()
