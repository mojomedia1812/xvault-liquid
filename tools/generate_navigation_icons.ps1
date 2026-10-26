param([string]$SkinRoot = (Join-Path $PSScriptRoot '../skin.xvault.liquid'))

Add-Type -AssemblyName System.Drawing
$bitmap = [System.Drawing.Bitmap]::new(128, 128, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$pen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(238, 255, 255, 255), 8)
$pen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
try {
    $graphics.DrawLines($pen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(20, 58), [System.Drawing.Point]::new(64, 22),
        [System.Drawing.Point]::new(108, 58)
    ))
    $graphics.DrawLines($pen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(30, 52), [System.Drawing.Point]::new(30, 104),
        [System.Drawing.Point]::new(52, 104), [System.Drawing.Point]::new(52, 76),
        [System.Drawing.Point]::new(76, 76), [System.Drawing.Point]::new(76, 104),
        [System.Drawing.Point]::new(98, 104), [System.Drawing.Point]::new(98, 52)
    ))
    $bitmap.Save((Join-Path $SkinRoot 'media/icons/home.png'), [System.Drawing.Imaging.ImageFormat]::Png)
} finally {
    $pen.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
}
