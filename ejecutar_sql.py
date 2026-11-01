"""Uso: python ejecutar_sql.py consultas.sql --db database"""
import argparse
from sqlengine.executor import execute


def main():
    parser = argparse.ArgumentParser(description='Interprete SQL con almacenamiento en archivos')
    parser.add_argument('archivo', help='Archivo SQL que se desea ejecutar')
    parser.add_argument('--db', default='database', help='Directorio de la base de datos')
    args = parser.parse_args()
    try:
        with open(args.archivo, encoding='utf-8') as file:
            results = execute(file.read(), args.db)
        for result in results:
            if isinstance(result, tuple):
                columns, rows = result
                print(' | '.join(columns))
                print('-+-'.join('-' * len(column) for column in columns))
                for row in rows:
                    print(' | '.join('NULL' if value is None else str(value) for value in row))
                print(f'({len(rows)} fila(s))')
            else:
                print(result)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
