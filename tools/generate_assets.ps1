Add-Type -AssemblyName System.Drawing

$root = "C:\_codex\xvault-skin\skin.xvault.liquid"
$textureDir = Join-Path $root "media\textures"
$iconDir = Join-Path $root "media\icons"
$promoDir = Join-Path $root "media\promos"
$resourceDir = Join-Path $root "resources"

New-Item -ItemType Directory -Force -Path $textureDir, $iconDir, $promoDir, $resourceDir | Out-Null

function New-RoundedPath {
    param(
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )

    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $diameter = $Radius * 2
    $path.AddArc($X, $Y, $diameter, $diameter, 180, 90)
    $path.AddArc($X + $Width - $diameter, $Y, $diameter, $diameter, 270, 90)
    $path.AddArc($X + $Width - $diameter, $Y + $Height - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($X, $Y + $Height - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    return $path
}

function Save-Png {
    param(
        [System.Drawing.Bitmap]$Bitmap,
        [string]$Path
    )

    $Bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $Bitmap.Dispose()
}

function New-WhitePixel {
    $bitmap = [System.Drawing.Bitmap]::new(1, 1, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $bitmap.SetPixel(0, 0, [System.Drawing.Color]::White)
    Save-Png $bitmap (Join-Path $textureDir "white.png")
}

function New-GradientPng {
    param(
        [string]$Path,
        [int]$Width,
        [int]$Height,
        [string]$Direction,
        [int]$StartAlpha,
        [int]$EndAlpha
    )

    $bitmap = [System.Drawing.Bitmap]::new($Width, $Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $rectangle = [System.Drawing.Rectangle]::new(0, 0, $Width, $Height)
    $mode = [System.Drawing.Drawing2D.LinearGradientMode]::Horizontal
    if ($Direction -eq "Vertical") {
        $mode = [System.Drawing.Drawing2D.LinearGradientMode]::Vertical
    }

    $brush = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
        $rectangle,
        [System.Drawing.Color]::FromArgb($StartAlpha, 0, 0, 0),
        [System.Drawing.Color]::FromArgb($EndAlpha, 0, 0, 0),
        $mode
    )
    $graphics.FillRectangle($brush, $rectangle)
    $brush.Dispose()
    $graphics.Dispose()
    Save-Png $bitmap $Path
}

function New-GlassTexture {
    param(
        [string]$Path,
        [int]$Width,
        [int]$Height,
        [int]$Radius,
        [int]$Alpha,
        [bool]$Focus
    )

    $bitmap = [System.Drawing.Bitmap]::new($Width, $Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $rectangle = [System.Drawing.Rectangle]::new(0, 0, $Width, $Height)
    $shape = New-RoundedPath 4 4 ($Width - 8) ($Height - 8) $Radius

    $bottomAlpha = [Math]::Max(18, $Alpha - 58)
    $fill = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
        $rectangle,
        [System.Drawing.Color]::FromArgb($Alpha, 255, 255, 255),
        [System.Drawing.Color]::FromArgb($bottomAlpha, 14, 22, 34),
        [System.Drawing.Drawing2D.LinearGradientMode]::ForwardDiagonal
    )
    $graphics.FillPath($fill, $shape)
    $fill.Dispose()

    $shine = New-RoundedPath 18 12 ($Width - 36) ([Math]::Max(10, [int]($Height * 0.32))) ([Math]::Max(6, $Radius - 8))
    $shineAlpha = if ($Focus) { 110 } else { 58 }
    $shineBrush = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
        [System.Drawing.Rectangle]::new(0, 0, $Width, [Math]::Max(22, [int]($Height * 0.38))),
        [System.Drawing.Color]::FromArgb($shineAlpha, 255, 255, 255),
        [System.Drawing.Color]::FromArgb(0, 255, 255, 255),
        [System.Drawing.Drawing2D.LinearGradientMode]::Vertical
    )
    $graphics.FillPath($shineBrush, $shine)
    $shineBrush.Dispose()
    $shine.Dispose()

    $lineWidth = if ($Focus) { 5 } else { 2 }
    $edgeColor = if ($Focus) {
        [System.Drawing.Color]::FromArgb(228, 144, 242, 255)
    } else {
        [System.Drawing.Color]::FromArgb(98, 255, 255, 255)
    }
    $edgePen = [System.Drawing.Pen]::new($edgeColor, $lineWidth)
    $graphics.DrawPath($edgePen, $shape)
    $edgePen.Dispose()

    if ($Focus) {
        $glowPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(124, 0, 213, 255), 12)
        $graphics.DrawPath($glowPen, $shape)
        $glowPen.Dispose()
    }

    $shape.Dispose()
    $graphics.Dispose()
    Save-Png $bitmap $Path
}

function New-Icon {
    param(
        [string]$Name,
        [scriptblock]$Draw
    )

    $bitmap = [System.Drawing.Bitmap]::new(128, 128, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $pen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(238, 255, 255, 255), 8)
    $thinPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(205, 255, 255, 255), 4)
    $brush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(224, 255, 255, 255))

    & $Draw $graphics $pen $thinPen $brush

    $brush.Dispose()
    $thinPen.Dispose()
    $pen.Dispose()
    $graphics.Dispose()
    Save-Png $bitmap (Join-Path $iconDir "$Name.png")
}

function New-Promo {
    param(
        [string]$Path,
        [System.Drawing.Color]$StartColor,
        [System.Drawing.Color]$EndColor,
        [System.Drawing.Color]$AccentColor,
        [string]$Theme
    )

    $width = 1920
    $height = 1080
    $bitmap = [System.Drawing.Bitmap]::new($width, $height, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $rectangle = [System.Drawing.Rectangle]::new(0, 0, $width, $height)

    $background = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
        $rectangle,
        $StartColor,
        $EndColor,
        [System.Drawing.Drawing2D.LinearGradientMode]::ForwardDiagonal
    )
    $graphics.FillRectangle($background, $rectangle)
    $background.Dispose()

    $shade = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
        $rectangle,
        [System.Drawing.Color]::FromArgb(18, 255, 255, 255),
        [System.Drawing.Color]::FromArgb(222, 0, 0, 0),
        [System.Drawing.Drawing2D.LinearGradientMode]::Vertical
    )
    $graphics.FillRectangle($shade, $rectangle)
    $shade.Dispose()

    $light = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(64, $AccentColor.R, $AccentColor.G, $AccentColor.B))
    for ($i = 0; $i -lt 8; $i++) {
        $x = 560 + ($i * 115)
        $y = 160 + (($i % 3) * 64)
        $graphics.FillEllipse($light, $x, $y, 340, 340)
    }
    $light.Dispose()

    $linePen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(132, $AccentColor.R, $AccentColor.G, $AccentColor.B), 3)
    if ($Theme -eq "city") {
        for ($i = 0; $i -lt 22; $i++) {
            $x = 720 + ($i * 42)
            $buildingHeight = 250 + (($i * 37) % 360)
            $buildingBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(166, 6, 10, 17))
            $graphics.FillRectangle($buildingBrush, $x, $height - $buildingHeight - 80, 34, $buildingHeight)
            $buildingBrush.Dispose()
            if ($i % 3 -eq 0) {
                $graphics.DrawLine($linePen, $x + 18, $height - $buildingHeight - 80, $x + 18, $height - 96)
            }
        }
    } elseif ($Theme -eq "orbit") {
        for ($i = 0; $i -lt 6; $i++) {
            $graphics.DrawEllipse($linePen, 650 - ($i * 32), 200 + ($i * 34), 720 + ($i * 64), 320 + ($i * 30))
        }
        $planet = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(184, 12, 18, 28))
        $graphics.FillEllipse($planet, 1120, 360, 430, 430)
        $planet.Dispose()
    } else {
        $mountain = [System.Drawing.Drawing2D.GraphicsPath]::new()
        $points = @(
            [System.Drawing.Point]::new(520, 880),
            [System.Drawing.Point]::new(780, 480),
            [System.Drawing.Point]::new(940, 815),
            [System.Drawing.Point]::new(1100, 430),
            [System.Drawing.Point]::new(1440, 880)
        )
        $mountain.AddPolygon([System.Drawing.Point[]]$points)
        $mountainBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(190, 3, 7, 14))
        $graphics.FillPath($mountainBrush, $mountain)
        $mountainBrush.Dispose()
        $mountain.Dispose()
        for ($i = 0; $i -lt 8; $i++) {
            $graphics.DrawLine($linePen, 260 + ($i * 180), 884 + (($i % 2) * 8), 1720 - ($i * 75), 930 + (($i % 3) * 18))
        }
    }
    $linePen.Dispose()

    $glassPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(110, 255, 255, 255), 2)
    for ($i = 0; $i -lt 5; $i++) {
        $x = 700 + ($i * 155)
        $glass = New-RoundedPath $x (220 + ($i * 18)) 250 515 18
        $graphics.DrawPath($glassPen, $glass)
        $glass.Dispose()
    }
    $glassPen.Dispose()
    $graphics.Dispose()
    Save-Png $bitmap $Path
}

function New-SkinIcon {
    $bitmap = [System.Drawing.Bitmap]::new(512, 512, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias

    $shape = New-RoundedPath 20 20 472 472 96
    $fill = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
        [System.Drawing.Rectangle]::new(0, 0, 512, 512),
        [System.Drawing.Color]::FromArgb(255, 8, 18, 30),
        [System.Drawing.Color]::FromArgb(255, 31, 129, 151),
        [System.Drawing.Drawing2D.LinearGradientMode]::ForwardDiagonal
    )
    $graphics.FillPath($fill, $shape)
    $fill.Dispose()

    $edge = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(205, 190, 246, 255), 6)
    $graphics.DrawPath($edge, $shape)
    $edge.Dispose()
    $shape.Dispose()

    $font = [System.Drawing.Font]::new("Segoe UI Semibold", 112, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $brush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
    $format = [System.Drawing.StringFormat]::new()
    $format.Alignment = [System.Drawing.StringAlignment]::Center
    $format.LineAlignment = [System.Drawing.StringAlignment]::Center
    $graphics.DrawString("xV", $font, $brush, [System.Drawing.RectangleF]::new(0, 0, 512, 512), $format)

    $format.Dispose()
    $brush.Dispose()
    $font.Dispose()
    $graphics.Dispose()
    Save-Png $bitmap (Join-Path $resourceDir "icon.png")
}

New-WhitePixel
New-GradientPng (Join-Path $textureDir "gradient-left.png") 1100 1080 "Horizontal" 238 0
New-GradientPng (Join-Path $textureDir "gradient-bottom.png") 1920 520 "Vertical" 0 238
New-GradientPng (Join-Path $textureDir "gradient-top.png") 1920 300 "Vertical" 178 0
New-GlassTexture (Join-Path $textureDir "glass-panel.png") 780 330 28 76 $false
New-GlassTexture (Join-Path $textureDir "glass-panel-focus.png") 780 330 28 108 $true
New-GlassTexture (Join-Path $textureDir "dock.png") 1680 210 34 78 $false
New-GlassTexture (Join-Path $textureDir "tile.png") 240 166 26 62 $false
New-GlassTexture (Join-Path $textureDir "tile-focus.png") 260 188 30 116 $true
New-GlassTexture (Join-Path $textureDir "poster-card.png") 236 354 20 58 $false
New-GlassTexture (Join-Path $textureDir "poster-card-focus.png") 260 386 24 112 $true

New-Icon "tv" {
    param($graphics, $pen, $thinPen, $brush)
    $screen = New-RoundedPath 24 30 80 52 10
    $graphics.DrawPath($pen, $screen)
    $screen.Dispose()
    $graphics.DrawLine($thinPen, 64, 84, 64, 100)
    $graphics.DrawLine($thinPen, 44, 102, 84, 102)
}

New-Icon "movies" {
    param($graphics, $pen, $thinPen, $brush)
    $graphics.DrawRectangle($pen, 26, 32, 76, 58)
    for ($x = 34; $x -lt 96; $x += 18) {
        $graphics.DrawLine($thinPen, $x, 32, $x + 14, 48)
    }
    $graphics.DrawLine($thinPen, 30, 62, 98, 62)
}

New-Icon "music" {
    param($graphics, $pen, $thinPen, $brush)
    $graphics.DrawLine($pen, 74, 24, 74, 82)
    $graphics.DrawLine($pen, 74, 28, 100, 36)
    $graphics.FillEllipse($brush, 38, 76, 30, 24)
    $graphics.DrawLine($thinPen, 52, 78, 74, 72)
}

New-Icon "addons" {
    param($graphics, $pen, $thinPen, $brush)
    foreach ($point in @(@(28, 28), @(68, 28), @(28, 68))) {
        $tile = New-RoundedPath $point[0] $point[1] 32 32 8
        $graphics.DrawPath($pen, $tile)
        $tile.Dispose()
    }
    $graphics.DrawLine($pen, 76, 84, 96, 84)
    $graphics.DrawLine($pen, 86, 74, 86, 94)
}

New-Icon "search" {
    param($graphics, $pen, $thinPen, $brush)
    $graphics.DrawEllipse($pen, 30, 28, 54, 54)
    $graphics.DrawLine($pen, 74, 74, 100, 100)
}

New-Icon "settings" {
    param($graphics, $pen, $thinPen, $brush)
    for ($i = 0; $i -lt 8; $i++) {
        $angle = $i * [Math]::PI / 4
        $x1 = 64 + ([Math]::Cos($angle) * 35)
        $y1 = 64 + ([Math]::Sin($angle) * 35)
        $x2 = 64 + ([Math]::Cos($angle) * 47)
        $y2 = 64 + ([Math]::Sin($angle) * 47)
        $graphics.DrawLine($pen, [float]$x1, [float]$y1, [float]$x2, [float]$y2)
    }
    $graphics.DrawEllipse($pen, 38, 38, 52, 52)
    $graphics.DrawEllipse($thinPen, 56, 56, 16, 16)
}

New-Icon "power" {
    param($graphics, $pen, $thinPen, $brush)
    $graphics.DrawArc($pen, 34, 36, 60, 60, 38, 282)
    $graphics.DrawLine($pen, 64, 24, 64, 60)
}

New-Icon "files" {
    param($graphics, $pen, $thinPen, $brush)
    $folder = New-RoundedPath 22 40 84 58 10
    $graphics.DrawPath($pen, $folder)
    $graphics.DrawLine($thinPen, 28, 40, 48, 28)
    $graphics.DrawLine($thinPen, 48, 28, 68, 40)
    $folder.Dispose()
}

New-Icon "star" {
    param($graphics, $pen, $thinPen, $brush)
    $points = @()
    for ($i = 0; $i -lt 10; $i++) {
        $radius = if ($i % 2 -eq 0) { 42 } else { 18 }
        $angle = -[Math]::PI / 2 + ($i * [Math]::PI / 5)
        $points += [System.Drawing.PointF]::new(
            [float](64 + ([Math]::Cos($angle) * $radius)),
            [float](64 + ([Math]::Sin($angle) * $radius))
        )
    }
    $graphics.FillPolygon($brush, [System.Drawing.PointF[]]$points)
}

New-Promo (Join-Path $promoDir "01-night-city.png") ([System.Drawing.Color]::FromArgb(4, 8, 18)) ([System.Drawing.Color]::FromArgb(24, 74, 92)) ([System.Drawing.Color]::FromArgb(0, 218, 255)) "city"
New-Promo (Join-Path $promoDir "02-orbit-signal.png") ([System.Drawing.Color]::FromArgb(13, 10, 28)) ([System.Drawing.Color]::FromArgb(91, 42, 80)) ([System.Drawing.Color]::FromArgb(255, 172, 74)) "orbit"
New-Promo (Join-Path $promoDir "03-north-coast.png") ([System.Drawing.Color]::FromArgb(6, 24, 32)) ([System.Drawing.Color]::FromArgb(15, 76, 70)) ([System.Drawing.Color]::FromArgb(139, 255, 212)) "coast"
New-SkinIcon
