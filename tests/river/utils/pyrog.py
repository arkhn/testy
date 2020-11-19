from typing import List

import requests

# GraphQL requests should be prettified with :
#  - tabWidth set to 4 spaces
#  - printWidth set to stay under flake8's max line length (79)


class PyrogClient:
    def __init__(self, url, auth_header=None):
        self.url = url
        self.headers = {
            "content-type": "application/json",
            "Authorization": auth_header,
        }

    def run_graphql_query(self, request: str, variables=None):
        """
        This function queries a GraphQL endpoint
        and returns a json parsed response.
        """
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json={"query": request, "variables": variables},
            )
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to the Pyrog service")

        if response.status_code != 200:
            raise Exception(
                "Graphql query failed with returning code "
                f"{response.status_code}\n{response.json()}."
            )
        body = response.json()
        if "errors" in body:
            status_code = body["errors"][0].get("statusCode")
            error_message = body["errors"][0].get("message")
            if status_code == 401:
                raise Exception(error_message)
            if status_code == 403:
                raise Exception("You don't have the rights to perform this action.")
            raise Exception(
                "GraphQL query failed with errors: "
                f"{[err['message'] for err in body['errors']]}."
            )

        return body

    def create_template(self, name: str):
        request = """
            mutation createTemplate($name: String!) {
                createTemplate(name: $name) {
                    id
                }
            }
        """
        return self.run_graphql_query(request, variables={"name": name})

    def delete_template(self, id_: str):
        request = """
            mutation deleteTemplate($id: ID!) {
                deleteTemplate(id: $id) {
                    id
                }
            }
        """
        return self.run_graphql_query(request, variables={"id": id_})

    def create_source(self, name: str, template_name: str, mapping: str):
        request = """
            mutation createSource(
                $templateName: String!
                $name: String!
                $mapping: String
            ) {
                createSource(
                    templateName: $templateName
                    name: $name
                    mapping: $mapping
                ) {
                    id
                }
            }
        """
        source_resp = self.run_graphql_query(
            request,
            variables={
                "templateName": template_name,
                "name": name,
                "mapping": mapping,
            },
        )
        return source_resp["data"]["createSource"]["id"]

    def delete_source(self, id_: str):
        request = """
            mutation deleteSource($id: ID!) {
                deleteSource(sourceId: $id) {
                    id
                }
            }
        """
        return self.run_graphql_query(request, variables={"id": id_})

    def upsert_credentials(self, source_id: str, credentials: dict):
        request = """
            mutation upsertCredential(
                $sourceId: ID!
                $host: String!
                $port: String!
                $login: String!
                $password: String!
                $database: String!
                $owner: String!
                $model: String!
            ) {
                upsertCredential(
                    sourceId: $sourceId
                    host: $host
                    port: $port
                    login: $login
                    password: $password
                    database: $database
                    owner: $owner
                    model: $model
                ) {
                    id
                }
            }
        """
        return self.run_graphql_query(
            request, variables={**credentials, "sourceId": source_id}
        )

    def list_resources(self) -> List:
        request = """
            query s {
                sources {
                    id
                    resources {
                        id
                        definitionId
                    }
                }
            }
        """
        response = self.run_graphql_query(request)
        return [
            {"resource_id": resource["id"], "resource_type": resource["definitionId"]}
            for resource in response["data"]["sources"][0]["resources"]
        ]
