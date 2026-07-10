from __future__ import annotations

from enum import StrEnum


class ExecutionMode(StrEnum):
    NOVO_CALCULO = "novo_calculo"
    CORRIGIR_HISTORICO = "corrigir_historico"
    CORRIGIR_DATAS_E_HISTORICO = "corrigir_datas_e_historico"


MODE_LABELS = {
    ExecutionMode.NOVO_CALCULO: "Novo calculo por importacao",
    ExecutionMode.CORRIGIR_HISTORICO: "Corrigir historico em calculos existentes",
    ExecutionMode.CORRIGIR_DATAS_E_HISTORICO: "Corrigir datas e historico em calculos existentes",
}


def execution_mode_requires_model(mode: ExecutionMode) -> bool:
    return mode == ExecutionMode.NOVO_CALCULO


def execution_mode_requires_history_match(mode: ExecutionMode) -> bool:
    return mode != ExecutionMode.NOVO_CALCULO
