Sony α7 V Creative Look video LUTs · {version}
https://github.com/751K/sony-look-bridge

EN
These LUTs make S-Log3 footage imitate the tone of the α7 V Creative Looks in photos.
- 12 looks (ST PT NT VV VV2 FL IN SH BW Sepia FL2 FL3) x 2 input gamuts x 6 white-balance
  variants, 65^3 .cube (144 files), and 24 DaVinci Resolve DCTLs (*_WB.dctl) that blend the
  variants of a look by a White Balance slider.
- Pick the variant by the white balance the camera recorded for the footage:
    ST-2500K    about 2800K and below
    ST-3100K    about 2800K to 3600K
    ST-4300K    about 3600K to 4600K
    ST-4900K    about 4600K to 5100K
    ST-5300K    about 5100K to 6200K
    ST-7500K    about 6200K and above
  The camera's look colours and the S-Log3 to camera RGB relation both change with the white
  balance; each variant uses a ColorChecker measurement at its own white balance.
- DCTL: keep the DCTLs and the LUTs together in one folder inside Resolve's LUT folder, add the
  ResolveFX DCTL effect on the node and set White Balance K to the clip's white balance; the
  two neighbouring variants are blended linearly in mired.
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
- 12 种外观（ST PT NT VV VV2 FL IN SH BW Sepia FL2 FL3）× 2 种输入色域 × 6 种色温版本，
  65³ .cube，共 144 个；另附 24 个 DaVinci Resolve DCTL（*_WB.dctl），按 White Balance 滑块
  在同一外观的各版本之间过渡。
- 按相机记录的素材白平衡选择版本：
    ST-2500K    约 2800K 以下
    ST-3100K    约 2800K 至 3600K
    ST-4300K    约 3600K 至 4600K
    ST-4900K    约 4600K 至 5100K
    ST-5300K    约 5100K 至 6200K
    ST-7500K    约 6200K 以上
  相机外观的颜色与 S-Log3 至相机 RGB 的关系都随白平衡变化；每个版本都按该白平衡下的色卡实测生成。
- DCTL：将 DCTL 与 LUT 放在 Resolve LUT 目录下的同一文件夹中，在节点上添加 ResolveFX DCTL，
  将 White Balance K 设为素材的白平衡，相邻两个版本按 mired 线性过渡。
- 输入：S-Log3（10-bit CV / 1023），色域见文件名中的 S-Gamut3 或 S-Gamut3.Cine。
- 输出：Rec.709 原色，Gamma 2.4。不应再叠加 Log 至 Rec.709 或 ACES 输出转换。
- 中灰位置与常规 S-Log3 LUT 不同。
  输入：按测光 +1⅔ 档（相机显示 +1.7）拍摄的素材设计，18% 灰码值为 547/1023，而非 420/1023。
  实际曝光不同时，应在 LUT 之前调整曝光。
  输出：按照片的影调将 18% 灰置于 0.607，而非约 0.40，高光余量相应较少。
- DaVinci Resolve：使用 DaVinci YRGB 项目，不启用色彩管理；将 LUT 加在接收 S-Log3 素材的节点上，
  曝光和白平衡调整置于其前；插值选择 Tetrahedral。在 Mac 上选择 Rec.709-A 输出只改变文件标签。
- 生成原理见仓库 docs/video.md；manifest.json 和 validation.json 记录生成参数与 colour-science 独立校验结果。
