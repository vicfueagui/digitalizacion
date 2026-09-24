# Compatible con Windows PowerShell 2.0. Solo bootstrap; python_runtime.py decide el perfil.
param([string]$Raiz, [string]$Accion)
$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding
$OutputEncoding = [Console]::OutputEncoding
$Argumentos = @($args)
$Candidatos = @((Join-Path $Raiz '.venv\Scripts\python.exe'))
$Configuracion = Join-Path $Raiz 'python_ruta.txt'
if (Test-Path -LiteralPath $Configuracion) {
    $Valor = ([System.IO.File]::ReadAllText($Configuracion)).Trim().Trim('"')
    if ($Valor -and -not $Valor.Contains("`n")) { $Candidatos += $Valor }
}
if ($env:DIGITALIZACION_PYTHON) { $Candidatos += $env:DIGITALIZACION_PYTHON }
foreach ($Base in @('HKCU:\SOFTWARE\Python\PythonCore','HKLM:\SOFTWARE\Python\PythonCore','HKLM:\SOFTWARE\Wow6432Node\Python\PythonCore')) {
    foreach ($Tag in @('3.8','3.8-64')) {
        $Clave = Join-Path $Base ($Tag + '\InstallPath')
        if (Test-Path $Clave) {
            $Instalado = (Get-Item $Clave).GetValue('ExecutablePath')
            if (-not $Instalado) { $Instalado = Join-Path ((Get-Item $Clave).GetValue('')) 'python.exe' }
            $Candidatos += $Instalado
        }
    }
}
foreach ($Launcher in @((Join-Path $env:SystemRoot 'py.exe'),(Join-Path $env:LOCALAPPDATA 'Programs\Python\Launcher\py.exe'))) {
    if (Test-Path -LiteralPath $Launcher) {
        $Instalado = & $Launcher '-3.8' '-c' 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0 -and $Instalado) { $Candidatos += ([string]$Instalado).Trim() }
    }
}
$Perfil = 'legado'
if ($Accion -eq 'instalar') { $Perfil = 'instalar' }
foreach ($Candidato in ($Candidatos | Select-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $Candidato -PathType Leaf)) { continue }
    if ((Get-Item -LiteralPath $Candidato).Length -eq 0) {
        Write-Host ('Descartado: interprete de 0 bytes: ' + $Candidato)
        continue
    }
    try {
        $Elegido = & $Candidato (Join-Path $Raiz 'python_runtime.py') '--seleccionar' '--raiz' $Raiz '--perfil' $Perfil
        $Resultado = $LASTEXITCODE
    } catch { Write-Host 'El candidato no se pudo ejecutar.'; continue }
    if ($Resultado -ne 0 -or -not $Elegido) { continue }
    $Elegido = ([string]$Elegido).Trim()
    if (-not (Test-Path -LiteralPath $Elegido -PathType Leaf)) { continue }
    Write-Host ('Python comprobado: ' + $Elegido)
    # Una vez iniciada la acción nunca se repite con otro intérprete tras un error operativo.
    & $Elegido (Join-Path $Raiz 'lanzar.py') $Accion @Argumentos
    exit $LASTEXITCODE
}
Write-Host 'No se encontro Python 3.8.10 x64 compatible. Consulte MIGRACION_WINDOWS10.html.'
Write-Host 'Puede indicar la ruta completa de python.exe en python_ruta.txt, sin argumentos.'
exit 70
