from __future__ import annotations

import argparse
from pathlib import Path

from .app import Application


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automacao local do PJe-Calc")
    parser.add_argument("--gui", action="store_true", help="Abre a interface grafica")
    parser.add_argument("--probe", action="store_true", help="Executa o dom probe")
    parser.add_argument("--base-url", default=None, help="Sobrescreve a URL base do PJe-Calc")
    parser.add_argument("--probe-output", default=None, help="Diretorio de saida do probe")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    app = Application(base_url_override=args.base_url)

    if args.probe:
        output_dir = Path(args.probe_output) if args.probe_output else None
        result = app.run_probe(output_dir=output_dir)
        print(f"Probe salvo em: {result.output_dir}")
        print(f"Selectors locais: {result.selectors_file}")
        return 0

    app.run_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
