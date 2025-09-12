if __name__ == "__main__":
    import subprocess
    import sys

    commands = [
        ["pytest", "test/", "-v"],
        ["pytest", "test/", "--cov=src", "--cov-report=html"],
        ["pytest", "test/", "-m", "not slow", "--tb=short"]
    ]

    for cmd in commands:
        print(f"\nEjecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            sys.exit(result.returncode)

    print("\n✅ Todos los tests completados exitosamente!")
