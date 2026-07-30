import importlib
import ast
from pathlib import Path

from django.test import SimpleTestCase


SERIALIZER_MODULES = (
	"apps.devices.api.serializers",
	"apps.questions.api.serializers",
	"apps.responses.api.serializers",
	"apps.sessions.api.serializers",
	"apps.transcripts.api.serializers",
	"apps.users.api.serializers",
)


def _base_name(node):
	if isinstance(node, ast.Name):
		return node.id
	if isinstance(node, ast.Attribute):
		parent = _base_name(node.value)
		return f"{parent}.{node.attr}" if parent else node.attr
	return None


class SerializerBindingTests(SimpleTestCase):
	def test_api_serializers_do_not_redundantly_repeat_source_field_names(self):
		"""Catch redundant explicit source=<field_name> declarations before DRF binds fields."""
		offending_fields = []

		for module_path in SERIALIZER_MODULES:
			module = importlib.import_module(module_path)
			serializer_file = Path(module.__file__).resolve()

			with serializer_file.open("r", encoding="utf-8") as handle:
				tree = ast.parse(handle.read(), filename=str(serializer_file))

			for node in ast.walk(tree):
				if not isinstance(node, ast.ClassDef):
					continue

				class_bases = {_base_name(base) for base in node.bases}
				if not any(base_name and base_name.endswith(("ModelSerializer", "Serializer")) for base_name in class_bases):
					continue

				for item in node.body:
					if not isinstance(item, ast.Assign) or len(item.targets) != 1:
						continue

					target = item.targets[0]
					if not isinstance(target, ast.Name):
						continue

					if not isinstance(item.value, ast.Call):
						continue

					source_value = None
					for keyword in item.value.keywords:
						if keyword.arg == "source" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
							source_value = keyword.value.value
							break

					if source_value == target.id:
						offending_fields.append(f"{module_path}:{node.name}.{target.id}")

		self.assertEqual(
			offending_fields,
			[],
			msg=(
				"Remove redundant source=<field_name> declarations from these serializers: "
				+ ", ".join(offending_fields)
			),
		)


class ManagementCommandImportTests(SimpleTestCase):
	def test_session_audit_command_is_importable(self):
		"""Lightweight guard that the read-only audit command exists for manual review."""
		module = importlib.import_module(
			"apps.lecturers.management.commands.list_stale_test_sessions"
		)
		self.assertTrue(hasattr(module, "Command"))
