import logging

from utils.singleton import Singleton
from utils.log_decorator import log

from dao.db_connection import DBConnection
from business_object.liste_de_course import ListeDeCourses
from dao.ingredient_dao import IngredientDao
from business_object.ingredient import Ingredient


class ListeDeCourseDAO(metaclass=Singleton):
    """Classe contenant les méthodes pour interagir avec la liste de courses de la base"""

    @log
    def creerListeDeCourses(self, ListeDeCourse) -> bool:
        """Création d'une nouvelle liste de courses dans la base de données.

        Parameters
        ----------
        listeDeCourse : ListeDeCourse
             La liste de courses à créer
        Returns
        -------
        created : bool
        True si la création est un succès, False sinon.
        """
        res = None

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO liste_de_courses(id_user) "
                        "VALUES %(idUtilisateur)s, "
                        "RETURNING id_liste_de_courses;",
                        {"idUtilisateur": ListeDeCourse.idUtilisateur},
                    )
                res = cursor.fetchone()
        except Exception as e:
            logging.info(e)

        created = False
        if res:
            ListeDeCourse.idListeDecourses = res["id_liste_de_courses"]
            created = True

        return created

    @log
    def obtenirIdListeDeCourses(self, idUtilisateur):
        """Obtenir l'identifiant de la liste de courses d'un utilisateur.

        Parameters
        ----------
        idUtilisateur : int
             L'identifiant de l'utilisateur

        Returns
        -------
        created : bool
        True si l'identifiant est trouvé, False sinon.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id_liste_de_courses         "
                        "FROM liste_de_courses             "
                        "WHERE id_user = %(idUtilisateur)s;           ",
                        {"idUtilisateur": idUtilisateur},
                    )
                    res = cursor.fetchone()

        except Exception as e:
            logging.info(e)
            raise

        return res[0]

    @log
    def listerTous(self, idUtilisateur) -> list[ListeDeCourses]:
        """lister les listes de courses de l'utilisateur grâce à son id

        Parameters
        ----------
        idUtilisateur : int
              L'identifiant de l'utilisateur

        Returns
        -------
        ListeDeCourses : list[ListeDecourses]
            renvoie la liste de courses de l'utilisateur
            dans la base de données.
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT ing.nom , ingc.quantite           "
                        "FROM ingredient_courses ingc                 "
                        "JOIN liste_de_courses lc using (id_ingredient_courses)  "
                        "JOIN users u using (id_user) "
                        "JOIN ingredients ing using (id_ingredient)"
                        "WHERE id_user=%(idUtilisateur)s;  ",
                        {"idUtilisateur": idUtilisateur},
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logging.info(e)
            raise

        Listecourses = []

        if res:
            for row in res:
                liste_courses = Listecourses(idUtilisateur)
                ingredient = Ingredient(row["nom"])
                liste_courses.ajouterIngredient(ingredient, row["quantite"])
                Listecourses.append(liste_courses)

        return Listecourses

    @log
    def ajouterUnIngredient(self, idUtilisateur, IngredientQuantite) -> bool:
        """Ajoute un ingrédient dans la liste de courses.

        Parameters
        ----------

        IngredientQuantite : dict
            un dictionnaire d'ingrédients et leurs quantités
        idUtilisateur : int
            L'identifiant de l'utilisateur

        Returns
        -------
        bool
            True si l'ajout est un succès, False sinon.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    id_liste_de_courses = ListeDeCourseDAO().obtenirIdListeDeCourses(idUtilisateur)
                    res = []
                    for ingredient, quantite in IngredientQuantite.items():
                        id_ingredient = IngredientDao().obtenirIdParNom(ingredient)
                        cursor.execute(
                            "INSERT INTO  "
                            "ingredient_courses(id_ingredient,id_liste_de_courses,quantite)"
                            "VALUES (%(id_ingredient)s, %(id_liste_de_courses)s, %(quantite)s) "
                            "ON CONFLICT (id_liste_de_courses,id_ingredient) "
                            "DO UPDATE SET quantite=%(quantite)s "
                            "RETURNING id_ingredient_courses; ",
                            {
                                "id_ingredient": id_ingredient,
                                "id_liste_de_courses": id_liste_de_courses,
                                "quantite": quantite,
                            },
                        )
                        res = res.append(cursor.fetchone())
        except Exception as e:
            logging.info(e)

        created = False
        if len(res) == len(IngredientQuantite):
            created = True
        return created

    @log
    def retirerUnIngredient(self, idUtilisateur, Ingredient) -> bool:
        """Retire un ingrédient de la liste de courses.
        Parameters
        ----------
        idUtilisateur : int
            L'identifiant de l'utilisateur.
        Ingredient : Ingredient
            L'ingrédient à retirer.

        Returns
        -------
        bool
        True si le retrait est un succès, False sinon.
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    id_liste_de_courses = ListeDeCourseDAO().obtenirIdListeDeCourses(idUtilisateur)
                    # Supprimer l'ingrédient
                    cursor.execute(
                        "DELETE FROM ingredient_courses                  "
                        " WHERE id_ingredient=%(id_ingredient)s      "
                        "AND id_liste_de_courses=%(id_liste_de_courses)s ",
                        {
                            "id_ingredient": Ingredient.idIngredient,
                            "id_liste_de_courses": id_liste_de_courses,
                        },
                    )
                    res = cursor.rowcount
        except Exception as e:
            logging.info(e)

        return res == 1
