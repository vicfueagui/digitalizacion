"""Suite sintética y resultado estructurado para el ensayo local de oficina."""
import argparse
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.integrity import runtime_info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resultado', required=True, help='JSON nuevo con los resultados de esta ejecución')
    args = parser.parse_args()
    os.environ['DIGITALIZACION_PROBAR_FUENTES_PRIVADAS'] = '0'
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    outcome = {
        'entorno': runtime_info(),
        'ejecutadas': result.testsRun,
        'aprobadas': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped) - len(result.expectedFailures) - len(result.unexpectedSuccesses),
        'fallidas': len(result.failures), 'errores': len(result.errors), 'omitidas': len(result.skipped),
        'fallos_esperados': len(result.expectedFailures), 'exitos_inesperados': len(result.unexpectedSuccesses),
        'detalle_omitidas': [{'prueba': str(test), 'motivo': reason} for test, reason in result.skipped],
        'correcto': result.wasSuccessful(),
    }
    with Path(args.resultado).open('x', encoding='utf-8') as out:
        json.dump(outcome, out, ensure_ascii=False, indent=2)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
