"""Regression cases for the prelaunch publication boundary."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_site import build
from check_site import validate
from publication_policy import PUBLIC_FILES, validate_output


class PageValidationTests(unittest.TestCase):
    def test_reviewed_pages_are_accepted(self):
        validate((ROOT / "index.html").read_text())
        validate((ROOT / "404.html").read_text(), homepage=False)

    def test_duplicate_attributes_cannot_hide_payment_link(self):
        html = (ROOT / "index.html").read_text()
        for attrs in [
            'href="https://example.com/checkout" href="mailto:nexoraproductosdigitales@gmail.com"',
            'HREF="https://example.com/checkout" href="mailto:nexoraproductosdigitales@gmail.com"',
        ]:
            with self.subTest(attrs=attrs), self.assertRaises(ValueError):
                validate(html.replace("</body>", "<a " + attrs + ">Prueba</a></body>"))

    def test_contact_link_cannot_add_other_recipients(self):
        html = (ROOT / "index.html").read_text()
        for query in ["bcc=other@example.com", "to=other@example.com", "subject=Test%0ABcc:other@example.com"]:
            with self.subTest(query=query), self.assertRaises(ValueError):
                validate(html.replace("?subject=Consulta%20por%20Kit%20NEXORA", "?" + query))

    def test_checkout_delivery_and_scripts_are_blocked_on_both_pages(self):
        cases = [
            '<a href="https://example.com/checkout">Comprar</a>',
            '<a href="producto.xlsx" download>Descargar</a>',
            '<form action="/pay"></form>',
            '<script src="https://example.com/checkout.js"></script>',
            '<meta http-equiv="refresh" content="0;url=https://example.com">',
            '<a href="#" onclick="buy()">Comprar</a>',
        ]
        for filename, homepage in [("index.html", True), ("404.html", False)]:
            html = (ROOT / filename).read_text()
            for addition in cases:
                with self.subTest(page=filename, addition=addition), self.assertRaises(ValueError):
                    validate(html + addition, homepage=homepage)

    def test_duplicate_viewports_are_rejected(self):
        html = (ROOT / "index.html").read_text()
        with self.assertRaises(ValueError):
            validate(html + '<meta name="viewport" content="width=device-width">')


class PublicationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix="nexora_policy_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in PUBLIC_FILES | {"wrangler.jsonc"}:
            shutil.copyfile(ROOT / name, self.root / name)

    def change_config(self, change):
        file = self.root / "wrangler.jsonc"
        config = json.loads(file.read_text())
        change(config)
        file.write_text(json.dumps(config))

    def test_clean_build_contains_only_reviewed_files(self):
        build(self.root)
        validate_output(self.root)
        self.assertEqual({file.name for file in (self.root / "dist").iterdir()}, PUBLIC_FILES)

    def test_wrong_assets_directory_is_rejected_before_copy(self):
        self.change_config(lambda config: config["assets"].update(directory="."))
        with self.assertRaisesRegex(ValueError, "Publish dist only"):
            build(self.root)
        self.assertFalse((self.root / "dist").exists())

    def test_unsafe_404_is_rejected_before_copy(self):
        file = self.root / "404.html"
        file.write_text(file.read_text() + '<script src="https://example.com/checkout.js"></script>')
        with self.assertRaises(ValueError):
            build(self.root)
        self.assertFalse((self.root / "dist").exists())

    def test_weakened_headers_are_rejected_before_copy(self):
        file = self.root / "_headers"
        file.write_text(file.read_text().replace("form-action 'none'; ", ""))
        with self.assertRaisesRegex(ValueError, "response header changed"):
            build(self.root)
        self.assertFalse((self.root / "dist").exists())

    def test_unexpected_product_file_stops_build_without_deleting_it(self):
        output = self.root / "dist"
        output.mkdir()
        file = output / "producto.xlsx"
        file.write_bytes(b"unpublished test fixture")
        with self.assertRaisesRegex(ValueError, "unexpected files"):
            build(self.root)
        self.assertEqual(file.read_bytes(), b"unpublished test fixture")

    def test_output_symlink_cannot_escape_public_directory(self):
        (self.root / "dist").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            build(self.root)

    def test_source_symlink_is_rejected(self):
        file = self.root / "404.html"
        file.unlink()
        file.symlink_to(self.root / "index.html")
        with self.assertRaisesRegex(ValueError, "regular file"):
            build(self.root)

    def test_changed_artifact_is_detected(self):
        build(self.root)
        (self.root / "dist/index.html").write_text("changed after validation")
        with self.assertRaisesRegex(ValueError, "differs from"):
            validate_output(self.root)

    def test_backend_resources_cannot_be_added_accidentally(self):
        self.change_config(lambda config: config.update(r2_buckets=[{"binding":"FILES","bucket_name":"example"}]))
        with self.assertRaisesRegex(ValueError, "reviewed static deployment options"):
            build(self.root)

    def test_duplicate_configuration_keys_are_rejected(self):
        file = self.root / "wrangler.jsonc"
        file.write_text(file.read_text().replace('"directory": "./dist"', '"directory": ".", "directory": "./dist"'))
        with self.assertRaisesRegex(ValueError, "Duplicate Wrangler"):
            build(self.root)

    def test_optimized_python_cannot_disable_publication_checks(self):
        self.change_config(lambda config: config["assets"].update(directory="."))
        env = dict(os.environ, PYTHONPATH=str(ROOT / "scripts"))
        result = subprocess.run([sys.executable, "-O", "-c", "import sys; from build_site import build; build(sys.argv[1])", str(self.root)], env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Publish dist only", result.stderr)
        self.assertFalse((self.root / "dist").exists())


if __name__ == "__main__":
    unittest.main()
