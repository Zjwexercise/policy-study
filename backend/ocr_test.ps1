param([string]$ImagePath)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
}[0]

Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime] | Out-Null
[Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime] | Out-Null

$absPath = (Resolve-Path $ImagePath).Path
$fileTask = [Windows.Storage.StorageFile]::GetFileFromPathAsync($absPath)
$file = Await $fileTask ([Windows.Storage.StorageFile])

$streamTask = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
$stream = Await $streamTask ([Windows.Storage.Streams.IRandomAccessStream])

$decoderTask = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
$decoder = Await $decoderTask ([Windows.Graphics.Imaging.BitmapDecoder])

$bitmapTask = $decoder.GetSoftwareBitmapAsync()
$bitmap = Await $bitmapTask ([Windows.Graphics.Imaging.SoftwareBitmap])

$lang = [Windows.Globalization.Language]::new("zh-Hans-CN")
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
if (-not $engine) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
}

$ocrTask = $engine.RecognizeAsync($bitmap)
$result = Await $ocrTask ([Windows.Media.Ocr.OcrResult])

foreach ($line in $result.Lines) {
    Write-Output $line.Text
}
