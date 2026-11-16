Sony α7 V Creative Look video LUTs · {version}
https://github.com/751K/sony-look-bridge

EN
These LUTs make S-Log3 footage imitate the tone of the α7 V Creative Looks in photos.
- 12 looks (ST PT NT VV VV2 FL IN SH BW Sepia FL2 FL3) x 2 input gamuts x 3 white-balance
  variants, 65^3 .cube (72 files), and 24 DaVinci Resolve DCTLs (*_WB.dctl) that blend the
  three variants of a look by a White Balance slider.
- Pick the variant by the white balance of the footage:
    ST          daylight, about 5000K and above
    ST-4200K    about 4300K to 5000K
    ST-Warm     warm light, about 4300K and below
  The camera's look colours and the S-Log3 to camera RGB relation both change with the white
  balance; each variant uses a ColorChecker measurement at 6500K, 4200K or 2600K.
- DCTL: keep the DCTLs and the LUTs together in one folder inside Resolve's LUT folder, add the
  ResolveFX DCTL effect on the node and set White Balance K to the clip's white balance:
  Warm at 4100K and below, 4200K at 4640K, Daylight at 5400K and above, linear in mired between.
- Input: S-Log3 (10-bit CV / 1023), S-Gamut3 or S-Gamut3.Cine as named in the file.
- Output: Rec.709 primaries, Gamma 2.4. Do not add another Log-to-709 or ACES output transform.
- Mid-grey differs from conventional S-Log3 LUTs.
  Input: designed for footage exposed at +1 2/3 EV (+1.7 on the camera); 18% grey at
  547/1023 instead of 420/1023. For other exposures, adjust exposure before the LUT.
  Output: 18% grey at 0.607, as in the photos, instead of about 0.40; less highlight headroom.
- DaVinci Resolve: DaVinci YRGB project without colour management; apply the LUT on the node
  that receives the S-Log3 clip, with exposure and white balance corrections before it;
  Tetrahedral interpolation. Rec.709-A output on a Mac changes only the file tag.
- Generation notes: docs/video.md in the repository. manifest.json and validation.json record
  the generation parameters and an independent colour-science read-back.

中文
本 LUT 使 S-Log3 视频的输出模仿 α7 V 照片 Creative Look 的色调。
- 12 种外观（ST PT NT VV VV2 FL IN SH BW Sepia FL2 FL3）× 2 种输入色域 × 3 种色温版本，
  65³ .cube，共 72 个；另附 24 个 DaVinci Resolve DCTL（*_WB.dctl），按 White Balance 滑块
  在同一外观的三套版本之间过渡。
- 按素材的拍摄白平衡选择版本：
    ST          日光，约 5000K 以上
    ST-4200K    约 4300K 至 5000K
    ST-Warm     暖光，约 4300K 以下
  相机外观的颜色与 S-Log3 至相机 RGB 的关系都随白平衡变化；三套分别按 6500K、4200K、2600K
  的色卡实测生成。
- DCTL：将 DCTL 与 LUT 放在 Resolve LUT 目录下的同一文件夹中，在节点上添加 ResolveFX DCTL，
  将 White Balance K 设为素材的白平衡：4100K 及以下为暖光版，4640K 为 4200K 版，
  5400K 及以上为日光版，其间按 mired 线性过渡。
- 输入：S-Log3（10-bit CV / 1023），色域见文件名中的 S-Gamut3 或 S-Gamut3.Cine。
- 输出：Rec.709 原色，Gamma 2.4。不应再叠加 Log 至 Rec.709 或 ACES 输出转换。
- 中灰位置与常规 S-Log3 LUT 不同。
  输入：按测光 +1⅔ 档（相机显示 +1.7）拍摄的素材设计，18% 灰码值为 547/1023，而非 420/1023。
  实际曝光不同时，应在 LUT 之前调整曝光。
  输出：按照片的影调将 18% 灰置于 0.607，而非约 0.40，高光余量相应较少。
- DaVinci Resolve：使用 DaVinci YRGB 项目，不启用色彩管理；将 LUT 加在接收 S-Log3 素材的节点上，
  曝光和白平衡调整置于其前；插值选择 Tetrahedral。在 Mac 上选择 Rec.709-A 输出只改变文件标签。
- 生成原理见仓库 docs/video.md；manifest.json 和 validation.json 记录生成参数与 colour-science 独立校验结果。
