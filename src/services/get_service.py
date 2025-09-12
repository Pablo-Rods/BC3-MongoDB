from src.database.connection import MongoDBConnection


class GetService:
    def __init__(self):
        self.collection = "arbol_conceptos"

    def get_by_project(
        self,
        project: str
    ):
        with MongoDBConnection() as conn:
            arboles = conn.get_collection(self.collection)

            if arboles is not None:
                result = arboles.find_one({
                    "archivo_origen": project
                })
                return result
            return None
