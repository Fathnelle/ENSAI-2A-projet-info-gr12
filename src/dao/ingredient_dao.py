import logging

from utils.singleton import Singleton
from utils.log_decorator import log

from dao.db_connection import DBConnection

from business_object.ingredient import Ingredient


class IngredientDao(metaclass=Singleton):
    """Classe contenant les méthodes pour accéder aux Ingrédients de la base de données"""

    @log
    def ajouterIngredient(self, ingredient) -> bool:
        """Ajouter un ingrédient dans la base de données

        Parameters
        ----------
        ingredient : Ingredient
            ingrédient à ajouter

        Returns
        -------
        created : bool
            True si la création est un succès,
            False sinon
        """

        res = None

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    # Vérifier si l'ingrédient existe déjà
                    cursor.execute(
                        "SELECT id_ingredient FROM ingredients " "WHERE nom = %(nom)s; ",
                        {"nom": ingredient.nom},
                    )
                    existing_ingredient = cursor.fetchone()

                    if existing_ingredient:
                        logging.info(f"L'ingrédient '{ingredient.nom}' existe déjà dans la base.")
                        return False
                    # Si l'ingrédient n'existe pas, on l'ajoute
                    cursor.execute(
                        "INSERT INTO ingredients(nom) VALUES    "
                        "(%(nom)s)                             "
                        "RETURNING id_ingredient;               ",
                        {
                            "nom": ingredient.nom,
                        },
                    )
                    res = cursor.fetchone()

            if res is None:
                return False

        except Exception as e:
            logging.info(e)
            raise

        return bool(res)

    @log
    def obtenirTousLesIngredients(self) -> list[Ingredient]:
        """
        Lister tous les ingrédients

        Parameters
        ----------
        None

        Returns
        -------
        liste_ingredients : list[Ingredient]
            renvoie la liste de tous les ingrédients dans la base de données
        """

        liste_ingredients = []

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                              "
                        "FROM ingredients;                     "
                    )
                    res = cursor.fetchall()

                    if res:
                        for row in res:
                            ingredient = Ingredient(
                                idIngredient=row["id_ingredient"],
                                nom=row["nom"],
                            )

                            liste_ingredients.append(ingredient)

        except Exception as e:
            logging.info(e)
            raise

        return liste_ingredients

    @log
    def supprimerIngredient(self, ingredient: Ingredient) -> bool:
        """Suppression d'un ingredient dans la base de données

        Parameters
        ----------
        ingredient : Ingredient
            ingredient à supprimer de la base de données

        Returns
        -------
        bool :  True si l'ingrédient a bien été supprimé,
                False sinon
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM ingredients                     "
                        " WHERE id_ingredient=%(idIngredient)s;      ",
                        {"idIngredient": ingredient.idIngredient},
                    )
                    res = cursor.rowcount

        except Exception as e:
            logging.info(e)
            return False

        return res > 0

    @log
    def obtenirIdParNom(self, nom: str) -> int:
        """Récupérer l'id d'un ingrédient par son nom

        Parameters
        ----------
        nom : str
            nom de l'ingrédient

        Returns
        -------
        int or None : id de l'ingrédient, ou None si non trouvé
        """
        nom = nom.upper()
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id_ingredient FROM ingredients
                        WHERE UPPER(nom) = %(nom)s;
                        """,
                        {"nom": nom},
                    )
                    res = cursor.fetchone()
                    # print(f"Valeur envoyée par cursor.fetchone : {res}")
            if res:
                return res["id_ingredient"]
            else:
                logging.warning(f"L'ingrédient '{nom}' est introuvable dans la base de données.")
                return None

        except Exception as e:
            logging.error(f"Erreur lors de l'obtention de l'ID pour l'ingrédient '{nom}': {e}")
            return None
