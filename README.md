# floor3d-toolkit

> **Sweet Home 3D로 그린 우리 집 도면을 Home Assistant에 3D 평면도로 띄우기 위한 Python CLI 도구.**

<p align="center">
  <img src="https://raw.githubusercontent.com/redchupa/floor3d-toolkit/main/docs/images/hero.png" alt="floor3d-card 안에 렌더링된 30평형 아파트" width="640">
</p>

[![PyPI](https://img.shields.io/pypi/v/floor3d-toolkit.svg)](https://pypi.org/project/floor3d-toolkit/)
[![Python](https://img.shields.io/pypi/pyversions/floor3d-toolkit.svg)](https://pypi.org/project/floor3d-toolkit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

위 이미지처럼 우리 집 평면도를 HA 대시보드에 띄우고, 거실 조명을 클릭하면 실제로 ON/OFF가 되는 인터랙티브 3D 카드를 만들 수 있어요. 본 도구는 그 과정에서 가장 골치 아픈 **파일 변환 + 카드 설정** 단계를 한 줄로 줄여줍니다.

---

## 잠깐 — 두 가지 다른 방법이 있어요

Sweet Home 3D 도면을 HA에 띄우는 방법은 두 가지가 있어요. 본인 취향에 맞는 쪽을 고르세요.

| | **방법 A — 동적 3D** (이 가이드 ⭐) | **방법 B — 정적 PNG** |
|---|---|---|
| 결과물 | 회전·확대 가능한 3D 모델 | 미리 렌더된 2D 이미지 |
| 조명 ON/OFF | 실시간 광원 시뮬레이션 | ON/OFF 이미지 두 장 교체 |
| 무게 | 한 파일 9~12MB, GPU 사용 | 가벼움, 모바일 친화적 |
| HA 카드 | [floor3d-card](https://github.com/adizanni/floor3d-card) | HA 기본 picture-elements |
| SH3D 플러그인 | [adizanni/ExportToHASS](https://github.com/adizanni/ExportToHASS) | [shmuelzon/home-assistant-floor-plan](https://github.com/shmuelzon/home-assistant-floor-plan) |
| 이 toolkit | **필요** | 사용 안 함 |

**모바일 위주로 가볍게**라면 방법 B, **PC에서 인터랙티브 3D**가 좋으면 방법 A (이 가이드). 본 toolkit은 방법 A를 도와줍니다.

---

# 시작하기 — 처음부터 끝까지 가이드

처음 따라하시는 분 기준으로 약 **30분~1시간** 정도 걸려요 (도면 그리는 시간 제외). 도면을 처음부터 그려야 한다면 1~2시간 더.

차례:
- [0단계 — 필요한 것들](#0단계--필요한-것들)
- [1단계 — ExportToHASS 플러그인 설치](#1단계--exporttohass-플러그인-설치)
- [2단계 — Sweet Home 3D로 도면 그리기](#2단계--sweet-home-3d로-도면-그리기)
- [3단계 — HA 호환 형식으로 내보내기](#3단계--ha-호환-형식으로-내보내기)
- [4단계 — floor3d-toolkit 설치](#4단계--floor3d-toolkit-설치)
- [5단계 — GLB 파일로 패키징](#5단계--glb-파일로-패키징)
- [6단계 — Home Assistant에 업로드](#6단계--home-assistant에-업로드)
- [7단계 — floor3d-card 설치](#7단계--floor3d-card-설치)
- [8단계 — 카드 만들기 (조명 1개부터)](#8단계--카드-만들기-조명-1개부터)
- [9단계 — 조명 매핑 늘려가기](#9단계--조명-매핑-늘려가기)

---

## 0단계 — 필요한 것들

| | |
|---|---|
| **Sweet Home 3D** | 도면 그리는 무료 프로그램. [https://www.sweethome3d.com/download.jsp](https://www.sweethome3d.com/download.jsp) |
| **Python 3.11 이상** | toolkit 실행용. [https://www.python.org/downloads/](https://www.python.org/downloads/) (설치 시 "Add Python to PATH" 꼭 체크) |
| **Home Assistant** + **HACS** | 카드 띄울 곳. HACS 설치 가이드: [https://www.hacs.xyz/docs/use/download/download/](https://www.hacs.xyz/docs/use/download/download/) |

**Sweet Home 3D 사용 가이드 (한국어)**
- 📝 글로 보기: [ray 님 블로그](https://naver.me/xcg9imY8)
- 🎬 영상으로 보기: [YouTube 튜토리얼](https://youtu.be/6JMdpXlp1po?si=4PCwZQzDjKKhFDU9)

처음 SH3D 쓰시는 분은 위 자료부터 보고 도면 그리는 법 익히시는 걸 추천합니다.

---

## 1단계 — ExportToHASS 플러그인 설치

Sweet Home 3D에 별도 플러그인을 설치해야 도면을 HA용 형식으로 내보낼 수 있어요.

1. **플러그인 파일 다운로드**
   👉 https://github.com/adizanni/ExportToHASS/releases/latest/download/ExportToHASSPlugin.sh3p

2. **설치** — 다음 두 가지 중 편한 방법:
   - **방법 A (가장 쉬움)**: 다운로드한 `ExportToHASSPlugin.sh3p` 파일을 **더블 클릭** → Sweet Home 3D가 자동으로 설치
   - **방법 B**: Sweet Home 3D 실행 → 메뉴 `파일 → 환경설정 → 플러그인` (영문판은 `File → Preferences → Plugins`) → **Import...** 클릭 → `.sh3p` 파일 선택 (또는 SH3D 창에 드래그)

3. **Sweet Home 3D 완전 종료 후 다시 실행**

4. 확인 — 메뉴 `파일 → 내보내기` 안에 **`Home Assistant 호환 형식`** (또는 영문 `Export to Home Assistant`) 항목이 보이면 OK ✅

---

## 2단계 — Sweet Home 3D로 도면 그리기

본인 집 도면을 그려요. 처음이면 0단계의 한국어 가이드 자료 참고.

**최소한 갖춰야 할 것**:
- 벽 — 실제 도면 치수에 가깝게
- 가구 — 기본 카탈로그의 stock 모델 사용 권장
- **각 방·구역마다 천장 조명 1개 이상 배치** — `Lights` 카테고리에서 가져옴

### ⚠️ 조명 이름은 반드시 영문으로!

도면 안에서 각 조명을 클릭 → Properties → Name 에 **영문 이름**을 적어 주세요.

| ❌ 안 됨 | ✅ 됨 |
|---|---|
| `안방 조명` | `Bedroom Master Light` |
| `거실 메인` | `Living Main` |
| `주방 식탁` | `Kitchen Dining` |

이유: ExportToHASS 플러그인이 한글 mesh 이름을 정상 처리하지 못해요. 단, Home Assistant 안의 entity ID는 한글이어도 괜찮습니다 (다음 단계에서 영문 mesh ↔ 한글 entity 매핑하면 됨).

다 그렸으면 `myhome.sh3d` 같은 이름으로 저장하세요.

---

## 3단계 — HA 호환 형식으로 내보내기

방금 그린 도면을 HA용으로 변환합니다.

1. Sweet Home 3D에서 도면 열어 둔 상태에서 메뉴 `파일 → 내보내기 → Home Assistant 호환 형식`
2. 출력 폴더 선택 (예: 바탕화면에 `myhome_export` 폴더 만들고 선택)
3. 폴더 안에 여러 파일이 생성됨:
   ```
   myhome_export/
   ├── home.obj           ← 3D 모델 데이터
   ├── home.mtl           ← 색상·재질 정보
   ├── home_<...>.jpeg    ← 텍스처 이미지 14개+
   └── home.json          ← 부가 정보
   ```

여러 파일이 한 폴더에 다 있으면 OK. 다음 단계에서 한 파일로 합칠 거예요.

---

## 4단계 — floor3d-toolkit 설치

터미널(Windows: PowerShell, macOS: Terminal)을 열고 **Python 버전부터 확인**:

```bash
python --version
```

`Python 3.11.x` 이상이 나와야 합니다. 3.10 이하면 [Python 공식 사이트](https://www.python.org/downloads/) 에서 최신 버전 설치 (설치 시 **"Add Python to PATH" 꼭 체크**) 후 터미널 다시 열기.

설치:

```bash
pip install floor3d-toolkit
```

설치되면 확인:

```bash
floor3d-toolkit version
```

`floor3d-toolkit 0.0.1` 같이 버전이 나오면 OK ✅

> 💡 **`floor3d-toolkit: command not found` 또는 `floor3d-toolkit이 잘못된 명령어`** 나오면 (Windows에서 자주 발생) — 터미널 한 번 닫았다가 다시 열고 시도. 그래도 안 되면 아래 형태로 명령 앞에 `python -m floor3d_toolkit.cli` 를 붙여 쓰면 됩니다:
> ```bash
> python -m floor3d_toolkit.cli version
> python -m floor3d_toolkit.cli pack home.obj -o dist/home.glb
> ```
>
> 💡 **`pip install`에서 권한 오류**가 나면 `pip install --user floor3d-toolkit` 으로 시도하세요.

---

## 5단계 — GLB 파일로 패키징

3단계에서 만든 여러 파일을 **한 개의 `.glb` 파일**로 묶습니다.

```bash
cd C:\Users\<본인>\Desktop\myhome_export
floor3d-toolkit pack home.obj -o dist/home.glb
```

(`cd` 명령으로 3단계의 폴더로 이동 후 `pack` 명령 실행)

> 💡 `cd` 한 다음 폴더 안에 `home.obj`가 진짜 있는지 확인하고 싶다면:
> - Windows: `dir`
> - macOS / Linux: `ls`
>
> `home.obj`, `home.mtl`, `home_*.jpeg` 들이 보여야 합니다.

성공하면 `dist/` 안에 두 파일이 만들어져요:

| 파일 | 용도 |
|---|---|
| `home.glb` | 텍스처가 임베드된 3D 모델 한 파일 (~10MB). 다음 단계에서 HA에 올릴 파일. |
| `home.nodes.txt` | 모델 안의 mesh 노드 이름 목록. 8단계 카드 만들 때 참고할 파일. |

**`home.nodes.txt` 살짝 열어 보면** 이런 내용:
```
light_living_main_light
light_kitchen_main_light
light_bedroom_master_light
furn_refrigerator_1
furn_sofa_1
Flat_TV_1
...
```

이 이름들이 카드 YAML에서 조명·가구 클릭 가능하게 만들 때 쓰이는 ID들이에요. 잘 보관해 두세요.

---

## 6단계 — Home Assistant에 업로드

`dist/home.glb` **하나만** HA의 `/config/www/floor3d/` 폴더로 복사하세요.

업로드 방법은 본인 HA 셋업에 따라 다양:
- **Samba addon** 설치한 경우: Windows 탐색기로 `\\<HA-IP>\config\www\floor3d\` 들어가서 복사
- **File editor addon** 설치한 경우: HA 좌측 메뉴 File editor → `/config/www/floor3d/` 폴더에 업로드
- **SSH 가능한 경우**: `scp dist/home.glb root@<HA-IP>:/config/www/floor3d/`

폴더가 없으면 만들어 주세요 (`www`, `floor3d` 둘 다).

업로드 후 브라우저로 다음 URL 접속해서 파일이 다운로드되면 OK:
```
http://<HA-IP>:8123/local/floor3d/home.glb
```

---

## 7단계 — floor3d-card 설치

HA 안에서 카드 라이브러리를 설치해요.

1. HA 좌측 메뉴 **HACS** 클릭
2. 상단의 **Dashboard** 탭 선택 (HACS 카테고리: Integration / **Dashboard** / Template / Theme 중)
3. 우상단 검색창에 `floor3d-card` 입력 → 결과 클릭
4. 우하단 **DOWNLOAD** 버튼 클릭
5. **브라우저 새로고침** (HA 재시작은 필수 아님)

> 💡 만약 검색 결과에 안 보이면, 우상단 점 3개 메뉴 → **Custom repositories** → `https://github.com/adizanni/floor3d-card` 추가 → Type: `Dashboard` 선택 → 저장 후 다시 검색.

---

## 8단계 — 카드 만들기 (조명 1개부터)

### 먼저 — 본인 HA의 entity_id 1개 찾기

카드 YAML에 박을 본인 entity_id (예: `light.living_room_main`)를 어디서 보는지 모를 수 있어요. 가장 쉬운 방법:

1. HA 좌측 메뉴 **개발자 도구 (Developer Tools)** 클릭
2. 상단 **상태 (States)** 탭
3. 검색창에 `light.` 입력 → 본인 집 조명 entity 목록이 나옴
4. 거실 메인 조명을 찾아서 그 entity ID (예: `light.living_room_ceiling`) 메모

> 💡 entity_id가 `switch.xxx` 인 경우도 매우 흔합니다 (스마트 스위치/플러그). `switch.` 로도 검색해서 확인.

### 카드 YAML 붙여넣기

> 💡 **중요**: 한 번에 24개 조명 다 매핑하지 마세요. 일단 **1개만** 잘 작동하는지 확인 후 늘려나가는 게 가장 빠릅니다.

대시보드 편집 → 카드 추가 → **수동** (목록 맨 아래) → 아래 YAML 붙여넣기:

```yaml
type: custom:floor3d-card
path: /local/floor3d/
objfile: home.glb
shadow: 'yes'
extralightmode: 'yes'
globalLightPower: 0.25
entities:
  - entity: light.living_room_main         # ← 본인 HA의 실제 light 엔티티 ID로
    type3d: light
    object_id: light_living_main_light     # ← home.nodes.txt 에서 복사
    action: more-info
    light:
      lumens: 1000
      color: '#ffffff'
      distance: 400
      shadow: 'yes'
      vertical_alignment: bottom
```

**채워야 할 두 곳**:

1. `entity:` 옆 → 본인 HA에 실제 존재하는 light/switch entity ID
   (예: `light.living_room_main`, `switch.kitchen_light` 등)

2. `object_id:` 옆 → `home.nodes.txt` 파일에서 매칭되는 mesh node 이름 복사
   (보통 `light_` 로 시작하는 이름)

저장 → **3D 평면도가 떠야 합니다**. 거실 조명 클릭 → ON/OFF 토글 → 평면도의 조명 영역 색이 바뀌면 성공 ✅

---

## 9단계 — 조명 매핑 늘려가기

8단계의 1개 조명이 잘 작동하면, 같은 패턴으로 다른 조명을 한 줄씩 추가:

```yaml
entities:
  # 거실 메인 (8단계에서 만든 것)
  - entity: light.living_room_main
    type3d: light
    object_id: light_living_main_light
    action: more-info
    light: { lumens: 1000, color: '#ffffff', distance: 400, shadow: 'yes', vertical_alignment: bottom }

  # 주방 메인 추가
  - entity: switch.kitchen_main
    type3d: light
    object_id: light_kitchen_main_light
    action: more-info
    light: { lumens: 1000, color: '#ffffff', distance: 400, shadow: 'yes', vertical_alignment: bottom }

  # 안방 추가
  - entity: light.bedroom_master
    type3d: light
    object_id: light_bedroom_master_light
    action: more-info
    light: { lumens: 1000, color: '#ffffff', distance: 400, shadow: 'yes', vertical_alignment: bottom }
```

**권장 흐름**:
1. 엔티티 1~2개 매핑 → 저장 → 작동 확인
2. 잘 되면 다음 5개 추가 → 저장 → 확인
3. 반복

이렇게 점진적으로 하면 오타가 어디서 났는지 추적이 쉬워요.

> ⚠️ **YAML 들여쓰기 주의**: YAML은 공백 개수가 엄격합니다. `- entity:` 앞에는 **공백 2개**, 그 안의 `entity:`, `type3d:` 등은 **공백 4개**. 위 예시 그대로 복사 + 값만 바꾸는 게 가장 안전합니다. 탭(`Tab`) 키 절대 쓰지 말고 **스페이스**로만.

### 라이트 위치를 시각적으로 확인하고 싶다면

"이 노드가 어느 방의 조명이지?" 헷갈리면 5단계에 옵션을 추가해서 다시 패키징:

```bash
floor3d-toolkit pack home.obj -o dist/home_debug.glb --show-light-fixtures
```

→ 카드에 조명 위치마다 작은 박스가 보여서 위치 파악이 쉬워집니다. 매핑 다 끝나면 옵션 빼고 다시 pack해서 깔끔한 버전으로 교체.

---

# 잘 안 될 때

### 카드가 안 뜨고 "Finished with errors" 빨간 박스만 보여요

브라우저에서 **F12** 누르면 콘솔이 열립니다. 빨간 에러 메시지 확인:

- `Entity not found` → 카드 YAML의 `entity:` ID가 실제 HA에 없음. 본인 entity ID 다시 확인.
- `Cannot read properties of null (reading 'color')` → 보통 `media_player`나 `sensor` 엔티티를 잘못 박았을 때. 일단 그 엔트리 삭제하고 다시 저장.

### 3D 화면이 안 뜨고 좌표축(빨강·초록·파랑 선)만 보여요

카드 YAML에 `camera_position`, `camera_target` 같은 카메라 옵션을 직접 넣었다면 다 빼세요. 그러면 floor3d-card가 자동으로 모델을 적당한 위치로 보여줍니다.

### 조명을 모두 켰는데 너무 환해서 평면도가 안 보여요

라이트 개당 `lumens` 값을 800~1000 사이로 + `globalLightPower: 0.25` (전역 어둡게). 그래도 환하면 lumens를 더 낮추세요.

### 조명이 다 꺼졌을 때 너무 어두워서 안 보여요

토킷의 기본 설정이라면 OFF 상태에서도 약간 자체 발광해서 보여야 합니다. 그래도 어두우면 카드 YAML의 `globalLightPower` 값을 0.4~0.6 으로 올려보세요.

### Sweet Home 3D의 `파일 → 내보내기` 메뉴에 `Home Assistant 호환 형식` 항목이 없어요

1단계의 플러그인 설치가 완료 안 됐어요. 다음 확인:
- 플러그인 파일이 정확한 위치에 있는지:
  - Windows: `%APPDATA%\eTeks\SweetHome3D\plugins\` 안에 `ExportToHASSPlugin.sh3p`
  - macOS: `~/Library/Application Support/eTeks/SweetHome3D/plugins/`
- Sweet Home 3D를 **완전히 종료 후** 다시 실행했는지

### 가구를 클릭해도 popup이 안 떠요

8단계 YAML의 `entities:` 에 그 가구가 매핑 안 되어 있어요. 다음과 같이 추가:

```yaml
- entity: media_player.living_tv         # 본인 TV 엔티티
  type3d: color
  object_id: Flat_TV_1                   # home.nodes.txt 에서 복사
  action: more-info
  colorcondition:
    - state: 'playing'
      color: '#ffc864'
    - state: 'paused'
      color: '#ffc864'
    - state: 'off'
      color: '#2d3a55'
    - state: 'idle'
      color: '#2d3a55'
```

`media_player` 처럼 상태가 on/off 가 아닌 엔티티는 위처럼 가능한 상태(`playing`, `paused`, `idle`, `off` 등)를 모두 적어줘야 카드가 안 깨져요.

---

# 보안 / 프라이버시

- 이 toolkit은 **100% 본인 컴퓨터에서만 동작**합니다. 도면 데이터를 외부 서버로 보내지 않아요.
- 단, 생성된 `.glb` 파일은 본인 집 구조를 담고 있으니 **공개 인터넷 (GitHub 공개 레포 등)에 절대 올리지 마세요**.

---

# 후원 💝

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

# License

[MIT](LICENSE) — 자유롭게 사용·수정·재배포 OK.

---

<details>
<summary><b>English summary</b></summary>

**floor3d-toolkit** packages Sweet Home 3D's `Export to Home Assistant` plugin
output (`home.obj` + `home.mtl` + 14 jpeg textures) into a single
texture-embedded `.glb` that drops straight into Home Assistant's
[`floor3d-card`](https://github.com/adizanni/floor3d-card).

### Prerequisites

1. [Sweet Home 3D](https://www.sweethome3d.com/download.jsp) (free / GPL)
2. [ExportToHASS plugin](https://github.com/adizanni/ExportToHASS/releases/latest) installed in Sweet Home 3D
3. Python 3.11+
4. Home Assistant with [HACS](https://www.hacs.xyz/) (for floor3d-card)

### Use

After drawing your floor plan in Sweet Home 3D (using **ASCII names only**
for light fixtures), export it via `File → Export → Export to Home Assistant`,
then:

```bash
pip install floor3d-toolkit
floor3d-toolkit pack home.obj -o dist/home.glb
```

The command also writes `dist/home.nodes.txt` listing every mesh node name.
Copy those names into your card YAML's `object_id` fields.

Upload `dist/home.glb` to `/config/www/floor3d/` in your HA, install
`floor3d-card` via HACS, and paste a card config that references
`/local/floor3d/home.glb`. See the full step-by-step in
[docs/tutorial-en.md](docs/tutorial-en.md).

MIT-licensed. Free OSS dependencies only.

</details>
