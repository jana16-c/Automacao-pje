# Automacao PJe em Python

1. Execute `Iniciar_AutomacaoPJE.bat`.
2. Na primeira vez, ele cria `.venv` e instala as dependencias.
3. Depois disso, a interface abre pelo `pythonw`, sem usar `.exe`.

Execucao manual:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\pythonw.exe .\AutomacaoPJE.pyw
```
