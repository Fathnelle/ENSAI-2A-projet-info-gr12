import logging

from utils.singleton import Singleton
from utils.log_decorator import log

from dao.db_connection import DBConnection

from business_object.recette import Recette
from business_object.ingredient import Ingredient
from dao.ingredient_dao import IngredientDao
from service.ingredient_service import IngredientService


class RecetteDao(metaclass=Singleton):
    """Classe contenant les méthodes pour accéder aux recettes de la base de données"""

    @log
    def ajouterRecette(self, recette: Recette) -> bool:
        """Ajout d'une recette dans la base de données"""

        res = None
        created = False

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO recettes(title, category, area, instructions)
                        VALUES (%(title)s, %(category)s, %(area)s, %(instructions)s)
                        RETURNING id_meal;
                        """,
                        {
                            "title": recette.titre,
                            "category": recette.categorie,
                            "area": recette.origine,
                            "instructions": recette.consignes,
                        },
                    )
                    res = cursor.fetchone()

        except Exception as e:
            logging.exception(e)
            raise

        if res:
            recette.idRecette = res["id_meal"]
            created = True

        if created:
            for ingredient, quantite in recette.ingredientQuantite.items():
                id_ingredient = IngredientDao().obtenirIdParNom(ingredient)
                if id_ingredient is None:
                    IngredientService().ajouterNouvelIngredient(ingredient)
                    id_ingredient = IngredientDao().obtenirIdParNom(ingredient)

                try:
                    with DBConnection().connection as connection:
                        with connection.cursor() as cursor:
                            # Vérifier si la relation existe déjà
                            cursor.execute(
                                "SELECT 1 FROM meals_ingredients "
                                "WHERE id_meal = %(id_meal)s"
                                " AND id_ingredient = %(id_ingredient)s; ",
                                {"id_meal": recette.idRecette, "id_ingredient": id_ingredient},
                            )
                            # Si la relation n'existe pas, insérer la ligne
                            if cursor.fetchone() is None:
                                cursor.execute(
                                    "INSERT INTO "
                                    "meals_ingredients(id_meal, id_ingredient, quantite)  "
                                    "VALUES (%(id_meal)s, %(id_ingredient)s, %(quantite)s); ",
                                    {
                                        "id_meal": recette.idRecette,
                                        "id_ingredient": id_ingredient,
                                        "quantite": quantite,
                                    },
                                )
                                logging.info(
                                    f"Ingrédient {ingredient} ajouté à la recette {recette.titre}."
                                )
                            else:
                                logging.info(
                                    f"La relation pour l'ingrédient {ingredient} existe déjà."
                                )
                except Exception as e:
                    logging.exception(e)
                    raise

        return created

    @log
    def obtenirToutesLesRecettes(self) -> list[Recette]:
        """Obtention de toutes les recettes de la base de données

        Returns:
        -------
        list[Recette]:
            Liste des recettes
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT r.id_meal, r.title, r.category, r.area, r.instructions,
                        mi.id_ingredient, i.nom, mi.quantite FROM recettes r
                        LEFT JOIN meals_ingredients mi ON r.id_meal = mi.id_meal
                        LEFT JOIN ingredients i ON mi.id_ingredient = i.id_ingredient;
                        """
                    )
                    res = cursor.fetchall()

        except Exception as e:
            logging.exception(e)
            raise

        recettes = []
        recettes_dict = {}

        if res:
            for row in res:
                id_meal = row["id_meal"]

                if id_meal not in recettes_dict:
                    recettes_dict[id_meal] = {
                        "idRecette": id_meal,
                        "titre": row["title"],
                        "categorie": row["category"],
                        "origine": row["area"],
                        "consignes": row["instructions"],
                        "ingredientQuantite": {},
                    }

                ingredient_name = row["nom"]
                quantite = row["quantite"]
                recettes_dict[id_meal]["ingredientQuantite"][ingredient_name] = quantite

            for recette_data in recettes_dict.values():
                recette = Recette(
                    idRecette=recette_data["idRecette"],
                    titre=recette_data["titre"],
                    categorie=recette_data["categorie"],
                    origine=recette_data["origine"],
                    consignes=recette_data["consignes"],
                    ingredientQuantite=recette_data["ingredientQuantite"],
                )
                recettes.append(recette)

        return recettes

    @log
    def obtenirRecettesparLettre(self, lettre) -> list[Recette]:
        """Rechercher des recettes commençant par une lettre donnée

        Parameters:
        ---------
        lettre : str
            Première lettre des recettes recherchées

        Returns:
        ------
        list[Recette] :
            Liste des recettes commençant par la lettre
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM recettes
                        WHERE nom ILIKE '%(lettre)s%'
                        """,
                        {
                            "lettre": lettre,
                        },
                    )
                    res = cursor.fetchall()

        except Exception as e:
            logging.exception(e)
            raise

        recettes = []

        if res:
            for row in res:
                recette = Recette(
                    idRecette=row["id_meal"],
                    titre=row["title"],
                    categorie=row["category"],
                    origine=row["area"],
                    consignes=row["instructions"],
                )
                recettes.append(recette)

        return recettes

    @log
    def obtenirRecettesParIngredient(self, ingredient: Ingredient) -> list[Recette]:
        """Obtention des recettes contenant un ingrédient spécifique

        Parameters
        ----------
        ingredient : Ingredient
            L'ingrédient contenu dans les recettes recherchées

        Returns
        -------
        List[Recette]
            Liste des recettes contenant l'ingrédient spécifié
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM recettes
                        JOIN recettes_ingredients ri ON r.id_meal = ri.id_meal
                        WHERE ri.id_ingredient = %(id_ingredient)s ;
                        """,
                        {"id_ingredient": ingredient.id_ingredient},
                    )
                    res = cursor.fetchall()

        except Exception as e:
            logging.exception(e)
            raise

        recettes = []

        if res:
            for row in res:
                recette = Recette(
                    idRecette=row["id_meal"],
                    titre=row["nom"],
                    categorie=row["categorie"],
                    origine=row["origine"],
                    consignes=row["instructions"],
                )
                recettes.append(recette)

        return recettes

    @log
    def obtenirRecettesParIngredients(self, ingredients: list[Ingredient]) -> list[Recette]:
        """Obtention de recettes contenant certains ingrédients

        Parameters:
        ---------
        ingredients : list[Ingredient]
            Liste des ingrédients contenus dans les recettes recherchées

        Returns:
        ------
        list[Recette] :
            Liste des recettes contenant les ingrédients voulus
        """

        ingredients_id = tuple([ing.idIngredient for ing in ingredients])

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:

                    cursor.execute(
                        """
                        SELECT * FROM recettes
                        JOIN meals_ingredients
                        ON meals_ingredients.id_meal = recettes.id_meal
                        WHERE meals_ingredients.id_ingredient IN %(ingredients_id)s
                        GROUP BY recettes.id_meal
                        """,
                        {
                            "ingredients_id": ingredients_id,
                        },
                    )
                    res = cursor.fetchall()

        except Exception as e:
            logging.exception(e)
            raise

        recettes = []

        if res:
            for row in res:
                recette = Recette(
                    idRecette=row["id_meal"],
                    titre=row["title"],
                    categorie=row["category"],
                    origine=row["area"],
                    consignes=row["instructions"],
                )
                recettes.append(recette)

        return recettes

    @log
    def obtenirRecettesParCategorie(self, categorie: str) -> list[Recette]:
        """Obtention de recettes par catégorie

        Parameters:
        ---------
        categorie : str
            Catégorie de recettes recherchées

        Returns:
        ------
        list[Recette] :
            Liste des recettes de la catégorie recherchée
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                            SELECT * FROM recettes
                            WHERE categorie = %(categorie)s;
                            """,
                        {"categorie": categorie},
                    )
                    res = cursor.fetchall()

        except Exception as e:
            logging.exception(e)
            raise

        recettes = []

        if res:
            for row in res:
                recette = Recette(
                    idRecette=row["id_meal"],
                    titre=row["nom"],
                    categorie=row["categorie"],
                    origine=row["origine"],
                    consignes=row["instructions"],
                )
                recettes.append(recette)

        return recettes

    @log
    def obtenirToutesLesCategories(self) -> list[str]:
        """Obtention de toutes les catégories de recettes de la base de données

        Returns:
        -------
        list[str]:
            Liste des catégories
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT DISTINCT category FROM recettes;
                        """
                    )
                    res = cursor.fetchall()

        except Exception as e:
            logging.exception(e)
            raise

        categories = []

        if res:
            for categorie in res:
                if categorie is not None:
                    categories.append(categorie)

        return categories
