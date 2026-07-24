param(
    [Parameter(Position=0)]
    [string]$FilePath = ""
)

$ErrorActionPreference = 'Stop'
# 用带 BOM 的 UTF-8 写文件，避免中文在中文 Windows 上被误判为 GBK 而乱码
$Utf8Bom = New-Object System.Text.UTF8Encoding($true)
$Inbox = Join-Path $env:USERPROFILE "ClipThinkInbox"
if (-not (Test-Path $Inbox)) { New-Item -ItemType Directory -Force -Path $Inbox | Out-Null }

function Get-Timestamp { return (Get-Date -Format "yyyyMMdd_HHmmss") }

if ($FilePath -ne "") {
    # 文件模式：把文件复制进收件箱并写索引
    if (Test-Path $FilePath) {
        $ts = Get-Timestamp
        $name = [System.IO.Path]::GetFileName($FilePath)
        $dest = Join-Path $Inbox $name
        if (Test-Path $dest) { $dest = Join-Path $Inbox ($ts + "_" + $name) }
        Copy-Item -Path $FilePath -Destination $dest -Force
        $md = Join-Path $Inbox ($ts + ".md")
        $rel = [System.IO.Path]::GetFileName($dest)
        $content = "# 待分析文件`n`n来源：$FilePath`n`n[$([System.IO.Path]::GetFileName($FilePath))](`"$rel`")`n"
        [System.IO.File]::WriteAllText($md, $content, $Utf8Bom)
        Write-Output $md
    } else {
        Write-Output "文件不存在: $FilePath"
    }
} else {
    # 剪贴板模式：图片或文字
    $ts = Get-Timestamp
    $img = $null
    try { $img = Get-Clipboard -Format Image } catch { }
    if ($null -ne $img) {
        try {
            $png = Join-Path $Inbox ($ts + ".png")
            $img.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
            $md = Join-Path $Inbox ($ts + ".md")
            $content = "# 待分析图片`n`n![clipboard](`"$($ts).png`")`n"
            [System.IO.File]::WriteAllText($md, $content, $Utf8Bom)
            Write-Output $md
        } catch {
            # 图片保存失败（如微信 DIB 等特殊剪贴板格式），回退到文字模式
            Write-Host "图片保存失败（回退到文字）: $_"
            $img = $null
        }
    }
    if ($null -eq $img) {
        $text = ""
        try { $text = Get-Clipboard -Raw } catch { }
        if ($text -and ($text.Trim() -ne "")) {
            $md = Join-Path $Inbox ($ts + ".md")
            $content = "# 待分析`n`n" + $text
        [System.IO.File]::WriteAllText($md, $content, $Utf8Bom)
        Write-Output $md
    } else {
        Write-Output "剪贴板为空或非文字/图片"
        }
    }
}
