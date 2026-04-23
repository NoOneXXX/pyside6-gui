# 设置双网卡，开机的时候执行一下桌面上的配置文件 
>[!tip]
>  ❗❗❗ 注意下面的clash设置，不要勾选tun mode，下面的bat文件名字起 🔥**network-split.ps1**🔥名字不一定要起一样的但是后缀必须是这个
[time:2026-04-07 11:28:19]

![图片](images/image_20260317_110532.png)

```bat
# ====== 网络接口 ======

$internal = "WLAN"
$external = "WLAN 2"

$internalGateway = "10.26.40.1"
$externalGateway = "192.168.176.77"

$internalIndex = (Get-NetAdapter -Name $internal).ifIndex
$externalIndex = (Get-NetAdapter -Name $external).ifIndex

Write-Host "内网网卡 index:" $internalIndex
Write-Host "外网网卡 index:" $externalIndex

# ====== 设置优先级 ======

Set-NetIPInterface -InterfaceAlias $external -InterfaceMetric 5
Set-NetIPInterface -InterfaceAlias $internal -InterfaceMetric 50

# ====== 删除默认路由 ======

Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Remove-NetRoute -Confirm:$false

# ====== 默认外网 ======

if (-not (Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue)) {

New-NetRoute `
-DestinationPrefix "0.0.0.0/0" `
-InterfaceIndex $externalIndex `
-NextHop $externalGateway `
-RouteMetric 5

}

# ====== 所有10网段走内网 ======

if (-not (Get-NetRoute -DestinationPrefix "10.0.0.0/8" -ErrorAction SilentlyContinue)) {

New-NetRoute `
-DestinationPrefix "10.0.0.0/8" `
-InterfaceIndex $internalIndex `
-NextHop $internalGateway

}

Write-Host ""
Write-Host "==============================="
Write-Host "网络分流完成"
Write-Host ""
Write-Host "外网 → WLAN2 + Clash"
Write-Host "所有10.* → WLAN + VPN"
Write-Host "==============================="
```
