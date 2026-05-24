# stltest — 3Dプリンタ空中造形プロジェクト

## プロジェクト概要

FDM 3Dプリンタで「空中造形」によるメッシュ円筒を作るためのGcode生成プロジェクト。
ノズルをX/Y/Z同時に動かし、空中に樹脂を吐出してダイヤモンド格子状のメッシュを形成する。

---

## ファイル構成

| ファイル | 内容 |
|----------|------|
| `visualize_mesh6.py` | 一筆書きサインカーブ設計の可視化（旧メイン） |
| `generate_gcode.py` | 一筆書き設計のGcode生成（Elegoo Neptune 4 Max用） |
| `cylinder_mesh.gcode` | 生成済みGcode |
| `visualize_zigzag.py` | **新設計**：層ごと三角波ジグザグの可視化（現在のメイン） |

---

## 設計の変遷

### 旧設計（visualize_mesh6.py / generate_gcode.py）

- **φ50mm × H50mm** の円筒
- **一筆書き（ワンパス）**：底面リング→0thプレ周回→メッシュ→トッププレ周回→上面リング
- **サインカーブ**でZ方向を上下
- プリンター：Elegoo Neptune 4 Max、ノズル1.8mm

#### 重要パラメータ

```python
NOZZLE_DIA    = 1.8
CIRCLE_DIA    = 50.0
TOTAL_HEIGHT  = 50.0
RING_HEIGHT   = 1.2
LAYER_HEIGHT  = 3.0
N_OSC_PER_REV = 18.5   # 必ず半整数！整数だとダイヤモンドメッシュにならない
OVERLAP       = 1.0    # mm 層間めり込み量
Z_AMP         = (LAYER_HEIGHT + OVERLAP) / 2  # = 2.0mm
PRINT_SPEED   = 5.0    # mm/s
# Flow: リング部100%、メッシュ部70%（M221）
```

#### 設計の核心ルール

1. **N_OSC_PER_REV は必ず半整数**（4.5, 9.5, 18.5…）
   - 半整数 → 1周ごとに位相が反転 → 隣の層のピークとバレーが交互に接触 → ダイヤモンド模様
   - 整数にするとメッシュにならない

2. **Z_AMP = (LAYER_HEIGHT + OVERLAP) / 2**
   - OVERLAP=0: ピークとバレーが点接触のみ → 3層目から空中造形になる
   - OVERLAP>0: 隣接層がめり込む → 確実に接触

3. **プレ周回のz_base変化幅は 2×Z_AMP**（LAYER_HEIGHTではない！）
   - OVERLAP=0のとき偶然 LAYER_HEIGHT = 2×Z_AMP で一致していたが、OVERLAP>0で崩れるバグがあった
   - 正しい式：0thプレ周回は `RING_HEIGHT - Z_AMP` → `RING_HEIGHT + Z_AMP`
   - トッププレ周回は `TOTAL_HEIGHT - Z_AMP` → `TOTAL_HEIGHT + Z_AMP`

4. **メッシュ終端とトッププレ周回の接続**
   - N_MESH_REVS は自動計算：`int((TOTAL_HEIGHT - RING_HEIGHT - 2*Z_AMP) / LAYER_HEIGHT)`
   - 端数はTransition区間（部分周回）で補完

---

### 新設計（visualize_zigzag.py）← 現在進行中

- **φ30mm × H30mm** の円筒
- **層ごと独立パス**：各層が閉じたループ、連続性不要
- **三角波（直線ジグザグ）**でZ方向を上下
- 各層の位相を明示的に交互設定するため、N_OSC_PER_REVは整数でOK

#### 現在のパラメータ

```python
CIRCLE_DIA    = 30.0
TOTAL_HEIGHT  = 30.0
LAYER_HEIGHT  = 5.0
N_OSC_PER_REV = 8      # 整数OK（層ごと独立なので位相を明示設定）
OVERLAP       = 1.0    # mm
Z_AMP         = (LAYER_HEIGHT + OVERLAP) / 2  # = 3.0mm
N_LAYERS      = 6
```

#### 位相設定

```python
phase_n = -np.pi/2 + n * np.pi  # 偶数層: -π/2（谷スタート）、奇数層: π/2（山スタート）
```

#### 三角波関数

```python
def triangle_wave(x):
    return (2 / np.pi) * np.arcsin(np.sin(x))
```

---

## 過去の失敗・知見

### 空中造形が崩れる原因と対策

| 症状 | 原因 | 対策 |
|------|------|------|
| 3層目から空中に吐出 | OVERLAP=0で点接触のみ、ピークが垂れると次層が届かない | OVERLAP=1.0mm以上 |
| 積み重なるごとにギャップが広がる | 垂れが蓄積 | OVERLAPをさらに増やす、速度を下げる |
| 樹脂が内側に倒れ込む | ブリッジが長すぎ | N_OSC_PER_REVを増やしてスパンを短縮 |
| 糸引き | 押し出し量 > スピードのバランス崩れ | フロー率を下げる |

### Bambu Lab P1Sでの失敗

- AMS搭載機はGcodeからのAMSローディング制御が困難
- `M106 S255` → `M106 P1 S255`（パーツ冷却ファン指定）
- フィラメントマッピングエラー：Bambu Studio独自メタデータヘッダーが必要
- → **結論：Bambu LabはSDカード直接印刷が確実**

---

## 印刷設定（Elegoo Neptune 4 Max）

```
ノズル径:    1.8mm
フィラメント: 1.75mm PLA
ノズル温度:  220°C
ベッド温度:  60°C
ベッド中心:  X210 Y210
印刷速度:   5mm/s（メッシュ部）
冷却ファン:  100%（M106 S255）
フロー:     リング100% / メッシュ70%（M221）
```

---

## 次のステップ

- [ ] `visualize_zigzag.py` の新設計でGcode生成スクリプトを作成
- [ ] 実際に印刷して接触・オーバーラップを確認
- [ ] OVERLAPの最適値を実験で決定（現在1.0mm）
