import requests

delete_source_mutation = """
mutation deleteSource($sourceId: ID!) {
    deleteSource(sourceId: $sourceId) {
        id
    }
}
"""
create_template_mutation = """
mutation createTemplate($name: String!) {
    createTemplate(name: $name) {
        id
    }
}
"""

create_source_mutation = """
mutation createSource($templateName: String!, $name: String!, $mapping: String) {
    createSource(templateName: $templateName, name: $name, mapping: $mapping) {
        id
    }
}
"""

upsert_credentials_mutation = """
mutation upsertCredential(
    $sourceId: ID!
    $host: String!
    $port: String!
    $login: String!
    $password: String!
    $database: String!
    $owner: String!
    $model: String!) {
        upsertCredential(
            sourceId: $sourceId
            host: $host
            port: $port
            login: $login
            password: $password
            database: $database
            owner: $owner
            model: $model) {
                id
    }
}
"""

sources_query = """
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

class PyrogClient:
    def __init__(self, url, auth_header=None):
        self.url = url
        self.headers = {
            "content-type": "application/json",
            "Authorization": auth_header,
        }

    def run_graphql_query(self, graphql_query, variables=None):
        """
        This function queries a GraphQL endpoint
        and returns a json parsed response.
        """
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json={"query": graphql_query, "variables": variables},
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
                f"GraphQL query failed with errors: {[err['message'] for err in body['errors']]}."
            )

        return body

    def delete_source(self, source_id):
        return self.run_graphql_query(delete_source_mutation, variables={"sourceId": source_id})

    def create_template(self, name):
        return self.run_graphql_query(create_template_mutation, variables={"name": name})

    def create_source(self, template_name, source_name, mapping):
        source_resp = self.run_graphql_query(create_source_mutation, variables={"templateName": template_name, "name": source_name, "mapping": mapping})
        return source_resp["data"]["createSource"]["id"]

    def upsert_credentials(self, source_id: str, credentials):
        return self.run_graphql_query(upsert_credentials_mutation, variables={**credentials, "sourceId": source_id})

    def get_resources(self):
        sources_resp = self.run_graphql_query(sources_query)

        return [
            {"resource_id": resource["id"], "resource_type": resource["definitionId"]}
            for resource in sources_resp["data"]["sources"][0]["resources"]
        ]
