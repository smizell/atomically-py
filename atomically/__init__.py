import copy
from urllib.parse import urlparse

import inflection
import yaml


class Atomically:
    def __init__(self, content):
        self.content = content
        self.generator = AtomicGenerator(self)

    @classmethod
    def from_file(cls, filename):
        with open(filename, "r") as f:
            content = yaml.safe_load(f)
        return cls(content)

    def generate(self):
        return self.generator.generate()


class AtomicGenerator:
    def __init__(self, atomic):
        self.atomic = atomic

    def generate(self):
        openapi = self.base_openapi()
        atomic_ext = AtomicExt(openapi)
        self._generate_operations_from_stacks(openapi, atomic_ext)
        return openapi

    def base_openapi(self):
        base_openapi = copy.deepcopy(self.atomic.content)
        return OpenAPI(base_openapi)

    def _generate_operations_from_stacks(self, openapi, atomic_ext):
        for stack in atomic_ext.stacks():
            tag_name = stack.readable_name()
            openapi.add_tag(tag_name)
            item_schema_name = f"{stack.name}Item"
            item_schema = self._generate_item_schema(stack)
            item_schema_ref = {"$ref": f"#/components/schemas/{item_schema_name}"}
            openapi.add_schema(item_schema_name, item_schema)
            collection_schema_name = f"{stack.name}Collection"
            collection_schema = self._generate_collection_schema(item_schema_name)
            collection_schema_ref = {
                "$ref": f"#/components/schemas/{collection_schema_name}"
            }
            openapi.add_schema(collection_schema_name, collection_schema)
            if stack.is_supported("create"):
                create_url = f"/{stack.computer_name_plural()}"
                create_http_method = "post"
                create_operation_id = f"create_{stack.computer_name()}"
                create_operation = openapi.add_operation(
                    create_url,
                    create_http_method,
                    create_operation_id,
                    f"Create {stack.name}",
                )
                create_operation.add_tag(tag_name)
                create_operation.add_request_body_json_schema(item_schema_ref)
                create_operation.add_response_json_schema(
                    201, "Created", item_schema_ref
                )
                self._add_error_responses(
                    openapi, create_operation, supported_errors=[400, 500]
                )
            if stack.is_supported("read"):
                path_parameter_name = f"{stack.computer_name()}_id"
                read_url = f"/{stack.computer_name_plural()}/{{{path_parameter_name}}}"
                read_http_method = "get"
                read_operation_id = f"read_{stack.computer_name()}"
                read_operation = openapi.add_operation(
                    read_url, read_http_method, read_operation_id, f"Read {stack.name}"
                )
                read_operation.add_tag(tag_name)
                read_operation.add_response_json_schema(200, "OK", item_schema_ref)
                read_operation.add_path_parameter(path_parameter_name)
                self._add_error_responses(openapi, read_operation)
            if stack.is_supported("update"):
                path_parameter_name = f"{stack.computer_name()}_id"
                update_url = (
                    f"/{stack.computer_name_plural()}/{{{path_parameter_name}}}"
                )
                update_http_method = "put"
                update_operation_id = f"update_{stack.computer_name()}"
                update_operation = openapi.add_operation(
                    update_url,
                    update_http_method,
                    update_operation_id,
                    f"Update {stack.name}",
                )
                update_operation.add_tag(tag_name)
                update_operation.add_request_body_json_schema(item_schema_ref)
                update_operation.add_response_json_schema(200, "OK", item_schema_ref)
                update_operation.add_path_parameter(path_parameter_name)
                self._add_error_responses(openapi, update_operation)
            if stack.is_supported("delete"):
                path_parameter_name = f"{stack.computer_name()}_id"
                delete_url = (
                    f"/{stack.computer_name_plural()}/{{{path_parameter_name}}}"
                )
                delete_http_method = "delete"
                delete_operation_id = f"delete_{stack.computer_name()}"
                delete_operation = openapi.add_operation(
                    delete_url,
                    delete_http_method,
                    delete_operation_id,
                    f"Delete {stack.name}",
                )
                delete_operation.add_tag(tag_name)
                delete_operation.add_response(204, "No content")
                delete_operation.add_path_parameter(path_parameter_name)
                self._add_error_responses(openapi, delete_operation)
            if stack.is_supported("list"):
                list_url = f"/{stack.computer_name_plural()}"
                list_http_method = "get"
                list_operation_id = f"list_{stack.computer_name()}"
                list_operation = openapi.add_operation(
                    list_url, list_http_method, list_operation_id, f"List {stack.name}"
                )
                list_operation.add_tag(tag_name)
                list_operation.add_response_json_schema(
                    200, "OK", collection_schema_ref
                )
                self._add_error_responses(openapi, list_operation)
                for stack_filter in stack.filters():
                    list_operation.add_parameter(stack_filter)
            for custom_operation in stack.custom_operations():
                if custom_operation.type() == "item":
                    custom_operation_url = f"/{stack.computer_name_plural()}/{{{path_parameter_name}}}/{custom_operation.url_path()}"
                    path_parameter_name = f"{stack.computer_name()}_id"
                    response_schema_ref = item_schema_ref
                else:
                    custom_operation_url = (
                        f"/{stack.computer_name_plural()}/{custom_operation.url_path()}"
                    )
                    path_parameter_name = None
                    response_schema_ref = collection_schema_ref
                custom_operation_http_method = "post"
                custom_operation_operation_id = (
                    f"{custom_operation.computer_name()}_{stack.computer_name()}"
                )
                operation = openapi.add_operation(
                    custom_operation_url,
                    custom_operation_http_method,
                    custom_operation_operation_id,
                    f"{custom_operation.name} {stack.name}",
                )
                operation.add_tag(tag_name)
                if path_parameter_name:
                    operation.add_path_parameter(path_parameter_name)
                if custom_operation.request_schema():
                    operation.add_request_body_json_schema(
                        custom_operation.request_schema()
                    )
                operation.add_response_json_schema(200, "OK", response_schema_ref)
                self._add_error_responses(openapi, operation)

    def _generate_item_schema(self, stack):
        schema = copy.deepcopy(stack.schema())
        schema["properties"]["id"] = {
            "type": "string",
            "description": "ID of the resource",
            "readOnly": True,
        }
        schema["properties"]["createdAt"] = {
            "type": "string",
            "format": "date-time",
            "description": "Date-time the resource was created",
            "readOnly": True,
        }
        schema["properties"]["updatedAt"] = {
            "type": "string",
            "format": "date-time",
            "description": "Date-time the resource was updated",
            "readOnly": True,
        }
        if "required" not in schema:
            schema["required"] = []
        schema["required"] += ["id", "createdAt", "updatedAt"]
        return schema

    def _generate_collection_schema(self, item_schema_name):
        return {
            "type": "object",
            "properties": {
                "nextUrl": {
                    "type": "string",
                    "format": "url",
                    "description": "Next link to be used with pagination",
                },
                "items": {
                    "type": "array",
                    "items": {"$ref": f"#/components/schemas/{item_schema_name}"},
                },
            },
            "required": ["items"],
        }

    def _add_error_responses(
        self, openapi, operation, supported_errors=[400, 404, 500]
    ):
        if not openapi.has_schema("Error"):
            openapi.add_schema(
                "Error",
                {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "URI reference that identifies the problem type",
                        },
                        "title": {
                            "type": "string",
                            "description": "A short, human-readable summary of the problem type",
                        },
                        "status": {
                            "type": "string",
                            "description": "The HTTP status code generated by the origin server for this occurrence of the problem.",
                        },
                        "detail": {
                            "type": "string",
                            "description": "A human-readable explanation specific to this occurrence of the problem",
                        },
                        "instance": {
                            "type": "string",
                            "description": "A URI reference that identifies the specific occurrence of the problem.  It may or may not yield further information if dereferenced",
                        },
                    },
                },
            )
        error_schema_ref = {"$ref": "#/components/schemas/Error"}
        if 400 in supported_errors:
            operation.add_response_json_schema(400, "Client error", error_schema_ref)
        if 404 in supported_errors:
            operation.add_response_json_schema(404, "Not found", error_schema_ref)
        if 500 in supported_errors:
            operation.add_response_json_schema(500, "Server error", error_schema_ref)


class AtomicExt:
    def __init__(self, openapi):
        self.openapi = openapi
        self.ext = openapi.get_ext("atomically") or {}

    def stacks(self):
        return [
            AtomicStack(self, stack_name, stack_content)
            for stack_name, stack_content in self.ext_stacks()
        ]

    def ext_stacks(self):
        return self.ext.get("stacks", {}).items()


class AtomicStack:
    def __init__(self, atomic_ext, name, content):
        self.openapi = atomic_ext.openapi
        self.atomic_ext = atomic_ext
        self.name = name
        self.content = content

    def readable_name(self):
        return inflection.humanize(self.name)

    def computer_name(self):
        return inflection.underscore(self.name)

    def computer_name_plural(self):
        return inflection.underscore(inflection.pluralize(self.name))

    def schema_ref(self):
        schema_ref = self.content.get("schema")
        if not schema_ref:
            return
        uri = schema_ref.get("$ref", "")
        return Reference.from_uri_string(uri)

    def schema(self):
        schema_ref = self.schema_ref()
        if not schema_ref.is_relative():
            raise TypeError("Only relative schemas are supported", schema_ref)
        if not self.openapi.is_schema_ref(schema_ref):
            raise TypeError("Must use a schema reference for atomic stacks", schema_ref)
        return self.openapi.get_schema(schema_ref.json_pointer())

    def filters(self):
        return self.content.get("filters", [])

    def default_supported(self):
        return ["create", "read", "update", "delete", "list"]

    def supported(self):
        return self.content.get("supported", self.default_supported())

    def is_supported(self, operation_name):
        return operation_name in self.supported()

    def custom_operations(self):
        custom_operations = self.content.get("custom", {})
        return [
            AtomicCustomOperation(self, custom_operation_name, custom_operation_content)
            for custom_operation_name, custom_operation_content in custom_operations.items()
        ]


class AtomicCustomOperation:
    def __init__(self, atomic_ext, name, content):
        self.atomic_ext = atomic_ext
        self.name = name
        self.content = content

    def type(self):
        return self.content.get("type", "item")

    def request_schema(self):
        return self.content.get("requestSchema")

    def url_path(self):
        return inflection.dasherize(self.name).lower()

    def computer_name(self):
        return inflection.underscore(self.name)


class Reference:
    def __init__(self, uri):
        self.uri = uri

    @classmethod
    def from_uri_string(cls, uri_string):
        return cls(urlparse(uri_string))

    def is_relative(self):
        return self.uri.path == ""

    def json_pointer(self):
        return JSONPointer.from_fragment(self.uri.fragment)


class JSONPointer:
    def __init__(self, parts):
        self.parts = parts

    @classmethod
    def from_fragment(cls, fragment):
        return cls(fragment.split("/")[1:])


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


class OpenAPI:
    def __init__(self, content):
        self.content = content

    def add_tag(self, name):
        self.ensure("tags", [])
        tag = {"name": name}
        self.content["tags"].append(tag)
        return tag

    def is_schema_ref(self, ref):
        json_pointer = ref.json_pointer()
        match json_pointer.parts:
            case ["components", "schemas", *_]:
                return True
            case _:
                return False

    def add_schema(self, name, schema):
        self.content["components"]["schemas"][name] = schema

    def has_schema(self, name):
        return name in self.content["components"]["schemas"]

    def get_schema(self, json_pointer):
        # TODO: better handling of the JSON Pointer here
        schema_name = json_pointer.parts[-1]
        return self.content["components"]["schemas"][schema_name]

    def add_operation(self, url, http_method, operation_id, summary=None):
        if "paths" not in self.content:
            self.content["paths"] = {}
        paths = self.content["paths"]
        if url not in paths:
            paths[url] = {}
        paths[url][http_method] = operation = {"operationId": operation_id}
        if summary:
            operation["summary"] = summary
        return Operation(operation)

    def to_yaml(self):
        return yaml.dump(self.content, Dumper=NoAliasDumper)

    def get_ext(self, ext_name):
        return self.content.get(f"x-{ext_name}")

    def ensure(self, property_name, default_value):
        if property_name in self.content:
            return
        self.content[property_name] = default_value


class Operation:
    def __init__(self, content):
        self.content = content

    def add_tag(self, tag_name):
        if "tags" not in self.content:
            self.content["tags"] = []
        self.content["tags"].append(tag_name)

    def add_path_parameter(self, name):
        if "parameters" not in self.content:
            self.content["parameters"] = []
        self.content["parameters"].append(
            {"in": "path", "name": name, "schema": {"type": "string"}, "required": True}
        )

    def add_parameter(self, parameter):
        if "parameters" not in self.content:
            self.content["parameters"] = []
        self.content["parameters"].append(parameter)

    def add_request_body_json_schema(self, request_body_schema):
        self.content["requestBody"] = {
            "content": {"application/json": {"schema": request_body_schema}}
        }

    def add_response(self, status_code, description):
        if "responses" not in self.content:
            self.content["responses"] = {}
        self.content["responses"][str(status_code)] = {"description": description}

    def add_response_json_schema(self, status_code, description, response_json_schema):
        if "responses" not in self.content:
            self.content["responses"] = {}
        self.content["responses"][str(status_code)] = {
            "description": description,
            "content": {"application/json": {"schema": response_json_schema}},
        }
