import argparse

from app.security.crypto import generate_key


def main() -> None:
    parser = argparse.ArgumentParser(prog="green-ocr")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("generate-key", help="Gera uma chave AES-256 para GREEN_OCR_ENCRYPTION_KEY")
    arguments = parser.parse_args()
    if arguments.command == "generate-key":
        print(generate_key())


if __name__ == "__main__":
    main()
