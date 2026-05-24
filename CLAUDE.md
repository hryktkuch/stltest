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

**能動パラメータ（ユーザーが決める値）**

| パラメータ | 値 | 意味 |
|---|---|---|
| `CIRCLE_DIA` | 30.0 mm | 円筒の直径 |
| `TOTAL_HEIGHT` | 30.0 mm | 円筒の全高 |
| `RING_HEIGHT` | 1.2 mm | 底面・上面リングの高さ（平面ベタ印刷） |
| `N_LAYERS` | 6 | ジグザグ層の数 |
| `N_OSC_PER_REV` | 8 | 1周あたりのジグザグ往復回数（整数必須） |
| `OVERLAP` | 1.0 mm | 隣接層へのめり込み量（接触保証マージン） |
| `NOZZLE_DIA` | 1.8 mm | ノズル径（押出し幅の基準） |
| `FILAMENT_DIA` | 1.75 mm | フィラメント径（E値計算に使用） |
| `PRINT_SPEED` | 2.5 mm/s | 印刷速度 |
| `NOZZLE_TEMP` | 220 °C | ノズル温度 |
| `BED_TEMP` | 60 °C | ベッド温度 |

**重要な受動パラメータ（自動計算・参照用）**

| パラメータ | 値 | 計算式 |
|---|---|---|
| `LAYER_HEIGHT` | 4.8 mm | `(TOTAL_HEIGHT - RING_HEIGHT) / N_LAYERS` |
| `Z_AMP` | 2.9 mm | `(LAYER_HEIGHT + OVERLAP) / 2` |
| ジグザグ傾斜角 | **44.56°** | `arctan(2×Z_AMP / (πD / N_OSC_PER_REV))` |

> ジグザグ傾斜角がほぼ45°のとき、上がり線と下がり線がほぼ直角に交差するダイヤモンド格子になる。
> `OVERLAP` や `N_OSC_PER_REV` を変えるとこの角度が変わる。

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

## CRITICAL チェックリスト（コード変更前に必ず確認）

### ⚠️ 各層の開始点は、前の層の頂点の真上でなければならない

各層は閉ループで、t=0（またはt=t_offset）から始まる。
偶数層は `phase_n = -π/2`（t=0でZ=谷）、奇数層は `phase_n = π/2`（t=0でZ=山）。

- **偶数層 n** は t=0 で谷 → 奇数層 n+1 は t=0 の直上を通るが、**奇数層 n+1 の t=0 は前の偶数層の「谷」の真上** → 空中スタートになってしまう
- **正しい対策**：奇数層を `t_offset = π / (2 × N_OSC_PER_REV)` だけずらして開始する
  - このオフセット点では前の偶数層のZ値が山（ピーク）になる → 支持面あり

```python
# 正しい実装
t_offset = (n % 2) * np.pi / (2 * N_OSC_PER_REV)
t = np.linspace(t_offset, t_offset + 2 * np.pi, PTS_PER_REV)
```

この修正を行わないと、奇数番目の層が常に空中から描画を開始し、造形が失敗する。

---

## 実験スクリプトの設計原則

### ⚠️ 実験では値を決め打ちしない

実験の目的は「何が良いかを物理的な結果から判断すること」。
Claudeには実際に何が起きるか判断できないため、以下を守ること：

- **パラメータは必ずコード冒頭にまとめて明示する**
- **「良さそう」という判断で値を固定しない** — 例：アプローチ距離8mm、オーバーラップ角8°などは全て実験変数にする
- **実験変数でないものも、変更しやすいように定数として切り出す**
- コード内に埋め込まれた数値（マジックナンバー）は禁止

#### 悪い例
```python
APPROACH_MM = 8.0   # 「良さそう」と決め打ち → NG
```

#### 良い例
```python
# ---- Experimental factors ----
APPROACH_VALS = [False, True]   # Factor C: アプローチあり/なし
APPROACH_MM   = 8.0             # アプローチありのときの距離（mm）← これ自体も将来的に実験変数にできる
```

---

## 実験計画（Phase構成）

### Phase 1b（現在）：ベース安定化 — `experiment_base.py`

**ファイル：** `experiment_base.gcode`

| Factor | 水準 |
|---|---|
| A: Z高さ（RING_HEIGHT） | 0.6 / 0.8 mm |
| B: 印刷速度 | 10 / 15 mm/s |
| C: アプローチ | なし / あり（8mm ラジアルアプローチ） |
| D: オーバーラップ | なし / あり（360°+8°） |

2×2×2×2 = 16コンボ。400×400mmベッドに4×4グリッドで配置。

**観察ポイント：**
- ベッドへの定着（剥がれないか）
- ダマの発生（Z高さと関係）
- 書き始めの荒れ（アプローチ・オーバーラップの効果）

**既知の問題（TODO）：**
- ヒゲ（stringing）：層間移動時の糸引き → リトラクト調整で対処予定
- ダマ（blob）：ノズル先端への樹脂溜まり → Phase 1bで最適Zを決めて解消を狙う

### Phase 2（予定）：1ストランドの空中造形

Phase 1b で最適な Z・速度が決まったら：
- Factor: DWELL_MS（頂点静止時間）
- Factor: N_OSC_PER_REV（スパン長さ）
- Factor: PRINT_SPEED（メッシュ印刷速度）

### Phase 3（予定）：層間オーバーラップ

Phase 2 でたわみ量が測れたら OVERLAP の最適値を決定。

---

## 次のステップ

- [ ] Phase 1b 印刷・観察
- [ ] OVERLAPの最適値を実験で決定（現在1.0mm）
