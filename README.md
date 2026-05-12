# floor3d-toolkit

> Sweet Home 3D 도면을 한 번에 Home Assistant **floor3d-card** 호환 `.glb`로 만들어 주는 Python CLI.

<p align="center">
  <img src="docs/images/hero.png" alt="floor3d-toolkit hero render" width="640">
</p>

[![tests](https://img.shields.io/badge/tests-20%20passed-brightgreen)](#개발)
[![python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 왜 이게 필요한가요?

[floor3d-card](https://github.com/adizanni/floor3d-card)를 시도해 본 분이라면 알 거예요 — 카드 자체는 멋진데 **세팅이 너무 번거롭다는 것**.

- Sweet Home 3D에서 `Export to Home Assistant` 누르면 `.obj` + `.mtl` + jpeg 14~20개 + `.json` 파일이 우르르 쏟아짐
- 그걸 일일이 `/config/www/floor3d/` 에 올리고
- mesh 노드 이름을 직접 확인해서
- 카드 YAML에 light/switch 엔티티를 24개 넘게 손으로 매핑

**floor3d-toolkit**은 이 과정을 다음과 같이 줄여 줍니다:

```bash
floor3d-toolkit pack home.obj -o home.glb
```

- 텍스처 14개를 **GLB 파일 하나에 임베드** → `/config/www/floor3d/` 에 1개 파일만 올리면 끝
- 라이트 픽스처는 자동으로 투명 처리 (깔끔한 룩) — 매핑 작업 중에는 `--show-light-fixtures`로 표시 가능
- emissive 베이스라인 자동 적용 (조명 OFF 시에도 평면도가 보임)
- 카드 YAML 자동 생성 + 휴리스틱 엔티티 제안

---

## 지원하는 두 가지 워크플로

| 명령 | 입력 | 결과 | 언제 쓸까 |
|---|---|---|---|
| **`pack`** ⭐ | Sweet Home 3D ExportToHASS 결과물 (`home.obj`+`home.mtl`+jpeg) | 텍스처 임베드 GLB | **추천** — 텍스처 살아 있는 예쁜 룩, 프로덕션 카드 |
| **`convert`** | `.sh3d` 직접 | 자체 변환 GLB (단색) | 빠른 프로토타입, 텍스처 불필요 시 |

처음 쓰는 분은 `pack` 으로 시작하세요.

---

## 빠른 시작 (5분)

### 1. 설치

```bash
pip install floor3d-toolkit
```

또는 개발용:

```bash
git clone https://github.com/redchupa/floor3d-toolkit
cd floor3d-toolkit
pip install -e ".[dev]"
```

### 2. Sweet Home 3D에서 도면 그리기 + 내보내기

1. [Sweet Home 3D](http://www.sweethome3d.com/) 무료 설치 (GPL OSS)
2. 평면도 그리기 (벽 + 가구 + **각 방마다 천장 조명**)
3. 조명 이름은 영문 또는 한글로 명확히 (예: `Living Main`, `안방 조명`)
4. 메뉴 `파일 → Export to Home Assistant` (애드온 설치 필요)
5. 출력 폴더 (예: `myhome_export/`) 에 `home.obj` + `home.mtl` + `home_*.jpeg` 등이 생성됨

### 3. GLB로 패키징

```bash
floor3d-toolkit pack myhome_export/home.obj -o dist/home.glb
```

`dist/home.glb` 한 파일에 모든 텍스처 임베드 (보통 9~12MB).

### 4. Home Assistant에 업로드

`dist/home.glb`를 HA의 `/config/www/floor3d/` 에 복사 (Samba/SSH/File editor 등).

### 5. floor3d-card 설정

HACS에서 `floor3d-card` 설치 후 Lovelace에 다음 카드 추가:

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
    object_id: light_living_main_light   # GLB 안의 mesh 노드 이름
    action: more-info
    light:
      lumens: 1000
      color: '#ffffff'
      distance: 400
      shadow: 'yes'
      vertical_alignment: bottom
  # ... 다른 조명들
```

→ **3D 평면도 + 실시간 조명 ON/OFF 시각화 완성** 🎉

---

## 매핑 작업 팁 — `--show-light-fixtures`

처음 매핑할 때 각 조명이 GLB 안에서 어떤 mesh 노드 이름인지 모르면 매핑이 막막합니다. 그땐:

```bash
floor3d-toolkit pack myhome_export/home.obj -o dist/home_debug.glb --show-light-fixtures
```

→ 조명 위치마다 작은 박스가 보여서 어느 방의 어느 조명인지 한눈에 확인. 매핑 완료 후 옵션 빼고 다시 pack하면 깔끔한 프로덕션 GLB.

---

## 완전 자동 워크플로 (`convert`)

`.sh3d` 파일에서 시작해서 엔티티 매핑 YAML + 카드 YAML 까지 한 번에 자동 생성하고 싶으면:

```bash
floor3d-toolkit convert myhome.sh3d \
  --output dist/ \
  --name home \
  --glb-url /local/floor3d/home.glb
```

생성되는 파일:

```
dist/
├── home.glb                       # floor3d-card가 읽는 3D 모델
├── home.obj / home.mtl            # 디버깅용
├── home.entity-mapping.yaml       # mesh ↔ HA entity 매핑 (편집 대상)
└── home.card-config.yaml          # Lovelace에 붙여넣는 카드 설정
```

`home.entity-mapping.yaml`에 본인 HA 엔티티 ID를 채워 넣고 `--mapping` 옵션으로 재실행하면 카드 config에 반영됩니다.

### `convert` 옵션

| 옵션 | 설명 |
|---|---|
| `--mapping <path>` | 사용자 매핑 YAML (mesh ↔ entity_id) |
| `--camera <preset>` | `iso` (기본) / `iso-far` / `iso-close` / `top` / `side` |
| `--light-preset <name>` | `warm` (기본) / `warm-bright` / `cool` / `daylight` / `subtle` |
| `--skip-furniture-meshes` | 가구를 박스로만 처리 (속도/용량 우선) |

자세한 가이드: [docs/tutorial-ko.md](docs/tutorial-ko.md) (한국어) | [docs/tutorial-en.md](docs/tutorial-en.md) (English)

---

## 핵심 설계 결정

- **mesh 노드 이름이 안정적** — 가구 추가/삭제 시에도 기존 이름 유지 → entity binding 안 깨짐
- **`transparent_slab_ceiling`** — floor3d-card의 light 누출 방지 천장 규약 자동 적용
- **emissive 베이스라인** — HA 조명이 모두 OFF여도 평면도 구조가 보이도록 자체 발광 18% 적용
- **도메인 인식 type3d** — `light`/`switch`/`binary_sensor`는 on/off, `media_player`는 playing/idle/paused, `fan`은 on/off 등 도메인별 colorcondition 자동
- **사용자 매핑만 카드에 출력 (`min_confidence=1.0`)** — 자동 휴리스틱 추측은 mapping yaml의 주석으로만 (존재하지 않는 엔티티 인한 floor3d-card 크래시 차단)

---

## 보안 / 프라이버시

본 패키지는 변환을 **100% 로컬에서 수행**합니다. 본인 도면 데이터를 외부로 전송하지 않습니다.

생성된 `.glb`/`.yaml` 파일은 본인 가옥 구조 정보를 담고 있으니 **공개 레포에 절대 커밋하지 마세요**. `.gitignore`가 기본적으로 `*.sh3d`, `*.obj`, `*.mtl`, `*.glb`, `myhome*` 패턴을 차단합니다.

`scripts/check_secrets.py` 가 평문 사설 IP / API 키 / 가족 실명 등을 패턴으로 차단합니다.

---

## 개발

```bash
pip install -e ".[dev]"
pytest          # 20 passed
ruff check .    # lint
python scripts/check_secrets.py
```

---

## 후원 💝

이 패키지가 도움이 되었다면 따뜻한 커피 한 잔 부탁드립니다.

- **토스**: `1000-1261-7813` (우*만)
- *"커피 한잔은 사랑입니다"* ☕

---

## License

[MIT](LICENSE)

---

<details>
<summary><b>English summary</b></summary>

**floor3d-toolkit** packages Sweet Home 3D's `ExportToHASS` output (OBJ + MTL + 14
jpeg textures) into a single texture-embedded `.glb` that drops straight into
Home Assistant's `floor3d-card`.

```bash
pip install floor3d-toolkit
floor3d-toolkit pack home.obj -o home.glb
```

- One file replaces 15+ scattered assets in `/config/www/floor3d/`.
- Light fixtures hidden by default for a clean look; `--show-light-fixtures`
  reveals them while you wire up `entity-mapping.yaml`.
- Emissive baseline keeps the floor plan readable even when all HA lights
  are off.
- Domain-aware `type3d` selection prevents floor3d-card crashes on
  `media_player`/`sensor` entities.

Also bundles a `convert` command that goes straight from `.sh3d` → glb +
entity-mapping.yaml + card-config.yaml.

MIT-licensed, free OSS dependencies only.

See [docs/tutorial-en.md](docs/tutorial-en.md) for the full walkthrough.

</details>
