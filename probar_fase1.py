"""Ejecutar desde la raíz: python probar_fase1.py archivo.sql --db database"""
import argparse
from sqlengine.phase1 import execute


def main():
    parser = argparse.ArgumentParser(description='Ejecutor SQL: fase 1')
    parser.add_argument('archivo', help='Archivo de sentencias SQL')
    parser.add_argument('--db', default='database', help='Directorio para los archivos de datos')
    args = parser.parse_args()
    try:
        with open(args.archivo, encoding='utf-8') as f:
            for message in execute(f.read(), args.db):
                print(message)
    except (OSError, ValueError) as e:
        parser.exit(1, f'Error: {e}\n')

if __name__ == '__main__':
    main()
