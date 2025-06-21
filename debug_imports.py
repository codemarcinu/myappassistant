import importlib
import os
import sys
import traceback


def test_imports():
    """
    Recursively finds all Python modules in the 'src/backend' directory
    and attempts to import them to check for import errors.
    """
    project_root = os.path.abspath(os.path.dirname(__file__))
    src_path = os.path.join(project_root, "src")

    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    backend_root = os.path.join(src_path, "backend")

    print(f"Project root: {project_root}")
    print(f"Source path: {src_path}")
    print(f"Backend root: {backend_root}")
    print("-" * 50)

    errors = []
    successes = []

    for root, _, files in os.walk(backend_root):
        for file in files:
            if file.endswith(".py"):
                # Construct the module path
                relative_path = os.path.relpath(os.path.join(root, file), src_path)
                module_name = os.path.splitext(relative_path.replace(os.sep, "."))[0]

                # Skip __init__ files if they are just for marking a package
                if (
                    file == "__init__.py"
                    and os.path.getsize(os.path.join(root, file)) == 0
                ):
                    continue

                try:
                    importlib.import_module(module_name)
                    print(f"✅ SUCCESS: {module_name}")
                    successes.append(module_name)
                except Exception as e:
                    error_msg = f"❌ FAILED: {module_name}\n{traceback.format_exc()}\n"
                    print(error_msg)
                    errors.append((module_name, str(e)))

    print("-" * 50)
    print(f"Total files checked: {len(successes) + len(errors)}")
    print(f"Successful imports: {len(successes)}")
    print(f"Failed imports: {len(errors)}")
    print("-" * 50)

    if errors:
        print("Summary of failed imports:")
        for module, error in errors:
            print(f"- {module}: {error}")
    else:
        print("🎉 All imports are working correctly!")


if __name__ == "__main__":
    test_imports()
