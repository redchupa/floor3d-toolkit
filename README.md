# floor3d-toolkit

> **Sweet Home 3D 도면을 Home Assistant `floor3d-card`에 깔끔하게 띄우기 위한 Python CLI.**
> Sweet Home 3D `ExportToHASS` 플러그인 결과물(`home.obj` + `home.mtl` + jpeg 텍스처 14개)을 텍스처 임베드된 `.glb` 한 파일로 패키징해서 HA에 바로 꽂아 쓸 수 있게 해 줍니다.

<p align="center">
  <img src="https://raw.githubusercontent.com/redchupa/floor3d-toolkit/main/docs/images/hero.png" alt="floor3d-card 안에 렌더링된 30평형 아파트" width="640">
</p>

[![PyPI](https://img.shields.io/pypi/v/floor3d-toolkit.svg)](https://pypi.org/project/floor3d-toolkit/)
[![Python](https://img.shields.io/pypi/pyversions/floor3d-toolkit.svg)](https://pypi.org/project/floor3d-toolkit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![tests](https://github.com/redchupa/floor3d-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/redchupa/floor3d-toolkit/actions/workflows/test.yml)

---

## 한 줄 요약

```bash
pip install floor3d-toolkit
floor3d-toolkit pack home.obj -o home.glb
```

→ HA의 `/config/www/floor3d/`에 `home.glb` 한 파일만 올리면 끝.

---

## 누구를 위한 도구인가요?

✅ Sweet Home 3D로 우리 집 평면도 그려 봤다
✅ Home Assistant `floor3d-card`를 시도해 봤는데 세팅이 너무 복잡해서 포기했다
✅ 클릭 한 번에 거실 조명 ON/OFF, 상태 한눈에 보이는 3D 대시보드를 갖고 싶다

---

## 잠깐 — 두 가지 다른 접근 방법이 있습니다

Sweet Home 3D 도면을 HA에 띄우는 방법은 사실 **두 가지 플러그인 + 두 가지 카드**가 존재해요. 본인 취향대로 선택하세요. 이 toolkit은 **방법 A** 전용입니다.

| | **방법 A — 동적 3D** (이 toolkit) | **방법 B — 정적 PNG** |
|---|---|---|
| SH3D 플러그인 | [adizanni/ExportToHASS](https://github.com/adizanni/ExportToHASS) | [shmuelzon/HomeAssistantFloorPlan](https://github.com/shmuelzon/home-assistant-floorplan) |
| HA 카드 | [floor3d-card](https://github.com/adizanni/floor3d-card) | HA 기본 [picture-elements](https://www.home-assistant.io/dashboards/picture-elements/) |
| 렌더 | 실시간 Three.js — 카메라 회전·확대 가능 | Sweet Home 3D가 미리 렌더한 PNG |
| 무게 | GLB 한 개 (~10MB), GPU 부하 있음 | PNG 여러 장, 매우 가벼움 |
| 조명 ON/OFF | 실시간 광원 시뮬레이션 | PNG 두 장 전환 (ON/OFF 미리 렌더) |
| 카메라 | 자유 회전 | 고정 (도면 그릴 때 각도 결정) |
| 이 toolkit 필요? | **예** — `pack` 명령으로 패키징 | 아니오 — `floorplan.yaml` 그대로 사용 |

→ **모바일에서 가볍게 보기 위주**면 방법 B(정적 PNG)도 좋은 선택이에요. 회전 가능한 **3D 인터랙티브**가 필요하면 방법 A.

---

## 왜 만들었나?

[floor3d-card](https://github.com/adizanni/floor3d-card)는 멋진 카드인데 **세팅이 진짜 번거롭습니다**:

| 기존 방식 | floor3d-toolkit 사용 |
|---|---|
| Sweet Home 3D + ExportToHASS → `home.obj` + `home.mtl` + jpeg 14개 + `home.json` 우르르 | `pack` 명령 한 번 → `home.glb` 하나 |
| HA의 `/config/www/floor3d/` 폴더에 모든 파일 업로드 | 한 파일만 업로드 |
| GLB 안의 mesh 노드 이름을 찾기 위해 Three.js 인스펙터 또는 Blender 사용 | `.nodes.txt` 자동 생성 — 복사·붙여넣기로 끝 |
| 카드 YAML에 24개+ 엔티티 매핑 손으로 작성 | `convert` 모드면 매핑 YAML 자동 생성 |
| 카드가 조명 OFF 상태면 진짜 캄캄해서 평면도 안 보임 | emissive 베이스라인 자동 적용 → 야간에도 식별 |
| `media_player` 엔티티 박으면 카드 크래시 (`Cannot read properties of null (reading 'color')`) | 도메인 인식 `type3d` + 자동 colorcondition으로 차단 |

---

## 사전 준비 — Sweet Home 3D 및 ExportToHASS 플러그인 설치

> 이 toolkit은 Sweet Home 3D의 **ExportToHASS 플러그인이 출력한 OBJ 번들**을 입력으로 받습니다. 따라서 두 가지 1회 설치가 필요합니다.

### 1) Sweet Home 3D 설치 (무료 GPL OSS)
- 다운로드: http://www.sweethome3d.com/download.jsp
- 한국어 사용 가이드 (글): [Sweet Home 3D 사용법 — ray 님](https://naver.me/xcg9imY8)
- 한국어 사용 가이드 (영상): [Sweet Home 3D 튜토리얼 YouTube](https://youtu.be/6JMdpXlp1po?si=4PCwZQzDjKKhFDU9)

### 2) ExportToHASS 플러그인 설치

별도 GitHub repo에서 `.sh3p` 파일 다운로드 후 Sweet Home 3D에 설치:

1. **플러그인 다운로드**: https://github.com/adizanni/ExportToHASS/releases/latest/download/ExportToHASSPlugin.sh3p
2. Sweet Home 3D 실행 → 메뉴 `파일 → 환경설정 → 플러그인` (또는 `File → Preferences → Plugins`)
3. **Import...** 또는 다운로드한 `.sh3p` 파일을 Sweet Home 3D 창에 드래그
4. Sweet Home 3D 재시작
5. 메뉴 `파일 → 내보내기` 안에 **`Home Assistant 호환 형식`** (또는 영문 `Export to Home Assistant`) 항목이 보이면 설치 완료

> 자세한 안내: https://github.com/adizanni/ExportToHASS

---

## 5분 워크플로

### 단계 1 — Sweet Home 3D로 도면 그리기

본인 집 도면 그리기. **각 방마다 천장 조명 하나 이상** 배치.

> ⚠️ **조명 이름은 반드시 영문으로 짓기** (예: `Living Main`, `Bedroom Master`). 한글 이름은 ExportToHASS 플러그인이 정상 처리하지 못합니다 (`light.한글` 형태의 HA entity ID는 OK, SH3D 안의 mesh **이름**만 영문).
>
> 한글 방 이름이 익숙하면 우선 도면은 영문 라벨로 그리고, 매핑 단계에서 본인 HA entity ID (한글 가능)와 연결하는 식으로 분리하세요.

### 단계 2 — Home Assistant 호환 형식으로 내보내기

- 메뉴 `파일 → 내보내기 → Home Assistant 호환 형식`
- 출력 폴더 선택 (예: `~/Desktop/myhome_export/`)
- 폴더 안에 다음 생성됨:
  ```
  home.obj
  home.mtl
  home_<여러>.jpeg
  home.json
  ```

### 단계 3 — toolkit으로 GLB 패키징

```bash
pip install floor3d-toolkit
cd ~/Desktop/myhome_export
floor3d-toolkit pack home.obj -o dist/home.glb
```

→ `dist/` 안에 두 파일:
- `home.glb` — 텍스처 임베드된 3D 모델 (보통 9~12MB)
- `home.nodes.txt` — GLB 안의 mesh 노드 이름 목록 (단계 5에서 사용)

### 단계 4 — Home Assistant에 업로드

HA의 `/config/www/floor3d/` 디렉터리에 `home.glb` 만 복사 (Samba addon / File editor addon / SCP 등).

### 단계 5 — floor3d-card 추가

HACS → Frontend → `floor3d-card` 검색 + 설치.

대시보드 편집 → 카드 추가 → 수동 → 다음 YAML 붙여넣기:

```yaml
type: custom:floor3d-card
path: /local/floor3d/
objfile: home.glb
shadow: 'yes'
extralightmode: 'yes'
globalLightPower: 0.25
entities:
  - entity: light.living_room_main
    type3d: light
    object_id: light_living_main_light   # ← home.nodes.txt 에서 복사
    action: more-info
    light:
      lumens: 1000
      color: '#ffffff'
      distance: 400
      shadow: 'yes'
      vertical_alignment: bottom
  # ... 본인 조명마다 추가
```

> `object_id` 는 단계 3에서 생성된 `home.nodes.txt` 의 이름 그대로 복사하세요. 천장 조명들은 `light_*` 접두사로 시작합니다.
> 라이트 위치가 GLB 안에서 정확히 어디인지 시각적으로 확인하고 싶으면 단계 3에 `--show-light-fixtures` 옵션 추가:
> ```bash
> floor3d-toolkit pack home.obj -o dist/home_debug.glb --show-light-fixtures
> ```
> 매핑 작업 다 끝나면 옵션 빼고 다시 pack → 라이트 박스 투명 처리된 깔끔한 GLB.

저장 → 3D 평면도가 떠야 합니다. 클릭하면 조명 토글, ON/OFF 상태가 실시간 반영 🎉

---

## sh3d 파일 직접 변환 모드 (`convert`)

ExportToHASS 플러그인 없이 `.sh3d` 파일 자체에서 시작하고 싶을 때:

```bash
floor3d-toolkit convert myhome.sh3d --output dist/ --name home
```

생성되는 파일:

```
dist/
├── home.glb                        # floor3d-card에 바로 꽂는 3D 모델
├── home.obj / home.mtl             # 디버깅용
├── home.entity-mapping.yaml        # 자동 생성된 매핑 템플릿 (수정 X — 출력 파일)
└── home.card-config.yaml           # Lovelace에 그대로 붙여넣는 카드 설정
```

### 본인 엔티티 매핑 적용 흐름 (⚠️ 입력 / 출력 yaml 분리 필수)

`home.entity-mapping.yaml`은 매 실행마다 **덮어씌워지는 출력 파일**입니다. 본인이 편집한 매핑은 **별도 입력 파일**로 분리해서 관리하세요:

```bash
# 1. 자동 생성된 매핑 파일을 입력용으로 복사
cp dist/home.entity-mapping.yaml dist/home.user-mapping.yaml

# 2. user-mapping.yaml 을 에디터로 열고 본인 HA entity_id 채워 넣기

# 3. --mapping 으로 user-mapping.yaml 지정해서 재변환
floor3d-toolkit convert myhome.sh3d \
  --output dist/ \
  --name home \
  --mapping dist/home.user-mapping.yaml
```

> 동일 path를 `--mapping`으로 넘기더라도 toolkit이 자동으로 `.bak` 백업을 만들지만, 입력/출력 분리가 가장 안전합니다.

### `convert` 옵션

| 옵션 | 설명 |
|---|---|
| `--mapping <path>` | 사용자 매핑 YAML (mesh ↔ entity_id) |
| `--camera <preset>` | `iso` (기본) / `iso-far` / `iso-close` / `top` / `side` |
| `--light-preset <name>` | `warm` (기본) / `warm-bright` / `cool` / `daylight` / `subtle` |
| `--skip-furniture-meshes` | 가구를 박스로만 처리 (속도/용량 우선) |
| `--glb-url <url>` | 카드 YAML이 가리킬 GLB URL (기본 `/local/floor3d/home.glb`) |

---

## 자주 묻는 질문 (Troubleshooting)

### Q. 카드가 안 뜨고 "Finished with errors" 만 보여요

브라우저 콘솔(F12) 열어서 에러 메시지 확인. 가장 흔한 원인:
- **`Entity not found`**: 카드 YAML의 entity_id가 HA에 실제 존재하지 않음. → 매핑 YAML에서 해당 줄 `null`로 바꾸기
- **`Cannot read properties of null (reading 'color')`**: `media_player`/`sensor` 같은 비표준 도메인을 `type3d: color`로 박았을 때. toolkit 출력 그대로 쓰면 발생 X (도메인 인식 자동 처리). 직접 카드 YAML 쓸 때 주의

### Q. 좌표축만 보이고 모델이 안 보여요

`camera_position` / `camera_target`이 잘못됐거나 너무 멀리. 카드 YAML에서 카메라 옵션 모두 빼고 floor3d-card의 자동 프레이밍에 맡기세요. `convert` 모드는 자동 산출, `pack` 모드는 카드 YAML에 카메라 미지정이 디폴트.

### Q. 모든 조명을 켰는데 화이트아웃

per-light `lumens`가 너무 강함. 500~1000 사이에서 시작 + `globalLightPower: 0.25` (전역 어둡게). 추천 시작값:
```yaml
globalLightPower: 0.25
shadow: 'yes'
extralightmode: 'yes'
# per-light
light:
  lumens: 1000
  color: '#ffffff'
  distance: 400
```

### Q. 조명 OFF 상태에서 너무 캄캄해요

toolkit으로 다시 pack — 자체 `emissive_factor: 0.18`이 모든 메시에 자체 발광을 부여해서 야간에도 식별 가능:
```bash
floor3d-toolkit pack home.obj -o home.glb
```

### Q. 라이트 위치 박스가 보여요 (작은 흰 점들)

매핑 디버깅용. 매핑 완료 후엔 옵션 빼고 다시 pack → 자동 투명:
```bash
floor3d-toolkit pack home.obj -o home.glb                       # 투명 (기본)
floor3d-toolkit pack home.obj -o home.glb --show-light-fixtures # 표시
```

### Q. SH3D `Tools` 메뉴에 Export to HASS 메뉴가 안 보여요

플러그인이 설치 안 됐거나 SH3D 재시작 필요. 다시 확인:
1. `%APPDATA%\eTeks\SweetHome3D\plugins\` (Windows) 또는 `~/Library/Application Support/eTeks/SweetHome3D/plugins/` (macOS)에 `ExportToHASSPlugin.sh3p` 있는지
2. SH3D 완전 종료 후 재시작
3. `Tools` 메뉴에 `Export obj to HASS` 보이면 OK

### Q. 매핑이 24개 넘게 있어서 작업이 너무 복잡해요

**한 번에 다 하지 마세요.** 흔한 실수가 카드 YAML을 24개 엔티티 전부 채워서 한꺼번에 저장하는 것. 그러다 한 곳 오타나면 카드 전체가 깨져요.

권장 흐름:
1. 우선 엔티티 1~2개만 매핑 → 카드 저장 → 동작 확인
2. 잘 되면 다음 5개 추가 → 다시 저장 → 확인
3. 단계별 누적

각 단계마다 콘솔(F12) 에러 한 줄씩 잡으면 디버깅이 훨씬 쉽습니다.

### Q. 가구 클릭 시 popup 안 떠요

엔티티 매핑이 안 되어 있는 노드는 클릭 비활성. 카드 YAML에 다음 형태로 추가:
```yaml
- entity: media_player.living_tv
  type3d: color
  object_id: Flat_TV_1
  action: more-info
  colorcondition:
    - state: 'playing'
      color: '#ffc864'
    - state: 'idle'
      color: '#2d3a55'
    - state: 'off'
      color: '#2d3a55'
```

---

## 보안 / 프라이버시

- 변환은 **100% 로컬**에서만 수행. 본인 도면 데이터가 외부 서버로 전송되는 일 없음.
- 생성된 `.glb`/`.yaml`은 본인 집 구조를 담고 있음 → **공개 레포에 절대 커밋하지 마세요**. `.gitignore`가 `*.sh3d`, `*.obj`, `*.mtl`, `*.glb`, `myhome*` 패턴을 기본 차단합니다.
- `scripts/check_secrets.py` 가 사설 IP / API 키 / 가족 실명 등을 패턴으로 차단 (선택 사용).

---

## 개발 / 기여

```bash
git clone https://github.com/redchupa/floor3d-toolkit
cd floor3d-toolkit
pip install -e ".[dev]"
pytest          # 20 passed
ruff check .
```

이슈/PR 환영합니다: https://github.com/redchupa/floor3d-toolkit/issues

---

## 후원 💝

이 패키지가 도움이 되었다면 따뜻한 커피 한 잔 부탁드립니다 🙏

<p align="center">
  <table align="center">
    <tr>
      <td align="center">
        <b>토스</b><br/>
        <img src="https://raw.githubusercontent.com/redchupa/floor3d-toolkit/main/docs/images/toss-donation.png" alt="Toss 후원 QR" width="220"/><br/>
        <code>1000-1261-7813</code> (우*만)
      </td>
      <td align="center">
        <b>PayPal</b><br/>
        <img src="https://raw.githubusercontent.com/redchupa/floor3d-toolkit/main/docs/images/paypal-donation.png" alt="PayPal 후원 QR" width="220"/>
      </td>
    </tr>
  </table>
</p>

*"커피 한잔은 사랑입니다"* ☕

---

## License

[MIT](LICENSE)

---

<details>
<summary><b>English summary</b></summary>

**floor3d-toolkit** packages Sweet Home 3D's `Export to Home Assistant` plugin
output (`home.obj` + `home.mtl` + 14 jpeg textures) into a single
texture-embedded `.glb` that drops straight into Home Assistant's
`floor3d-card`.

### Prerequisites

1. Sweet Home 3D (free / GPL): http://www.sweethome3d.com/download.jsp
2. ExportToHASS plugin (`.sh3p`): https://github.com/adizanni/ExportToHASS/releases/latest

### Use

```bash
pip install floor3d-toolkit
floor3d-toolkit pack home.obj -o home.glb
```

The command also writes `home.nodes.txt` next to the GLB, listing every mesh
node name. Copy those names into your card's `object_id` fields.

### Highlights

- One file replaces 15+ scattered assets in `/config/www/floor3d/`.
- Light fixtures hidden by default for a clean look;
  `--show-light-fixtures` reveals them while you wire up the card.
- Emissive baseline keeps the floor plan readable even when every HA light
  is off.
- Domain-aware `type3d` selection prevents floor3d-card crashes on
  `media_player` / `sensor` / `fan` entities.
- A `convert` command also goes straight from `.sh3d` → glb +
  `entity-mapping.yaml` + `card-config.yaml`, with automatic backup of
  user-edited mapping yaml on re-runs.

MIT-licensed. Free OSS dependencies only (`trimesh`, `pygltflib`, `lxml`,
`pyyaml`, `unidecode`, `networkx`, `scipy`).

</details>
