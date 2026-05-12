# 튜토리얼 — Sweet Home 3D 도면을 Home Assistant 3D 평면도로

> 처음부터 끝까지: Sweet Home 3D로 도면 그리기 → ExportToHASS로 내보내기 → `floor3d-toolkit`으로 패키징 → HA `floor3d-card`에 띄우기.

소요 시간: 도면 그리기 1~2시간 (한 번만), 변환·설정 10분.

---

## 0. 준비물

| | |
|---|---|
| Sweet Home 3D | 무료 GPL OSS — http://www.sweethome3d.com/download.jsp |
| ExportToHASS 플러그인 (`.sh3p`) | https://github.com/adizanni/ExportToHASS/releases/latest/download/ExportToHASSPlugin.sh3p |
| Python | 3.11+ |
| Home Assistant | + [HACS](https://hacs.xyz) (`floor3d-card` 설치용) |

### ExportToHASS 플러그인 설치 (1회)

1. 위 URL에서 `ExportToHASSPlugin.sh3p` 다운로드
2. Sweet Home 3D 실행 → `파일 → 환경설정 → 플러그인` (또는 `File → Preferences → Plugins`)
3. **Import...** 클릭 → 다운로드한 `.sh3p` 선택 (또는 SH3D 창에 드래그)
4. Sweet Home 3D 재시작
5. 메뉴 `파일 → 내보내기` 안에 **`Home Assistant 호환 형식`** 항목이 보이면 OK

---

## 1. 도면 그리기 (Sweet Home 3D)

1. Sweet Home 3D 실행, 새 프로젝트
2. 벽 그리기 — 실제 도면 치수대로
3. 가구 배치 — 기본 카탈로그의 stock 모델 사용 권장
4. **각 방·구역마다 천장 조명 1개 이상** 배치 — `Lights` 카테고리에서 가져옴
5. 조명 이름을 알아보기 쉽게 변경 (예: "Living Main Light", "안방 조명")
6. `myhome.sh3d`로 저장

### 조명 이름 짓는 팁

`ExportToHASS` 가 조명을 GLB의 mesh node로 변환할 때 이름이 매핑됩니다. 추후 카드 YAML 작성 시 이 mesh node 이름이 그대로 `object_id` 가 됩니다. 이름이 명확할수록 매핑이 쉬워요.

---

## 2. ExportToHASS로 내보내기

1. 메뉴 `파일 → 내보내기 → Home Assistant 호환 형식`
2. 출력 폴더 선택 (예: `~/Desktop/myhome_export/`)
3. 폴더 안에 생성되는 파일:
   ```
   home.obj
   home.mtl
   home_<여러>.jpeg     # 텍스처 14개+
   home.json            # mesh node ↔ 친화적 이름 매핑
   ```

---

## 3. floor3d-toolkit 설치 및 패키징

```bash
pip install floor3d-toolkit
cd ~/Desktop/myhome_export
floor3d-toolkit pack home.obj -o dist/home.glb
```

생성되는 파일:

```
dist/
├── home.glb          # floor3d-card에 꽂는 3D 모델 (텍스처 14개 임베드, ~10MB)
└── home.nodes.txt    # GLB 안의 mesh node 이름 목록 (다음 단계에서 사용)
```

### 옵션

| 옵션 | 설명 |
|---|---|
| `-o / --output` | 출력 GLB 경로 (기본 `dist/home.glb`) |
| `--show-light-fixtures` | 라이트 박스를 표시 (기본은 투명). 카드 매핑 작업 중 라이트 위치 확인용 |
| `--hide-light-fixtures` | 라이트 박스 투명 처리 (기본) |

---

## 4. Home Assistant에 업로드

`dist/home.glb` 한 파일을 HA의 `/config/www/floor3d/` 디렉터리에 복사. 방법은 편한 것:
- Samba addon
- File editor addon
- SCP/SSH

---

## 5. floor3d-card 설치 + 카드 추가

### 5-1. HACS에서 설치

HACS → Frontend → `floor3d-card` 검색 + 설치 + HA 재시작.

### 5-2. 카드 YAML 작성

대시보드 편집 → 카드 추가 → 수동 → 다음 YAML 시작점:

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
```

### 5-3. `object_id` 채우기

`dist/home.nodes.txt` 를 열면 GLB 안에 있는 모든 mesh node 이름이 나옵니다. 천장 조명은 보통 `light_*` 접두사:

```
light_living_main_light
light_kitchen_main_light
light_bedroom_master_light
furn_refrigerator_1
furn_sofa_1
Flat_TV_1
...
```

각 HA 엔티티마다 위 목록에서 가장 맞는 mesh node 이름을 골라 `object_id` 에 채워 넣으세요.

### 5-4. 라이트 위치를 시각적으로 확인하고 싶을 때

매핑 작업 중에 "이 노드가 어느 방의 어느 조명이지?" 헷갈리면, 단계 3을 `--show-light-fixtures` 옵션 켜서 다시:

```bash
floor3d-toolkit pack home.obj -o dist/home_debug.glb --show-light-fixtures
```

→ 카드에 작은 박스가 보여서 라이트 위치 한눈에 파악. 매핑 다 끝나면 옵션 빼고 다시 pack → 깔끔한 프로덕션 GLB.

---

## 6. 잘 안 될 때

| 증상 | 원인 / 해결 |
|---|---|
| 카드가 빨간 박스 "Finished with errors" | F12 콘솔 열어서 에러 메시지 확인. 보통 `Entity not found` (entity_id 오타) 또는 `Cannot read properties of null (reading 'color')` (media_player 등에 `type3d: color` + 부족한 colorcondition) |
| 좌표축만 보이고 모델 안 보임 | 카드 YAML에서 `camera_position` / `camera_target` 옵션 빼고 floor3d-card 기본 자동 프레이밍에 맡기기 |
| 모든 조명 켰는데 너무 화이트아웃 | per-light `lumens` 너무 강함. 500~800 사이로 낮추기 + `globalLightPower: 0.25` |
| 조명 OFF 상태에서 너무 캄캄 | `floor3d-toolkit pack` 으로 다시 패키징 (emissive_factor=0.18 자동 적용 — 야간에도 식별) |
| Sweet Home 3D에서 가구 추가했더니 매핑 깨짐 | 같은 이름 추가 시 `_1`, `_2` 접미사 생김. 이름 다르게 짓기 |

---

## 7. `convert` 모드 (Optional — ExportToHASS 없이 .sh3d 직접 변환)

ExportToHASS 플러그인 설치하기 싫거나 빠른 프로토타입만 보고 싶을 때:

```bash
floor3d-toolkit convert myhome.sh3d --output dist/ --name home
```

생성되는 파일:

```
dist/
├── home.glb
├── home.entity-mapping.yaml   # 자동 매핑 (출력 파일 — 매 실행 덮어씀)
└── home.card-config.yaml      # Lovelace에 붙여넣는 카드 설정
```

매핑을 본인 entity_id로 채우려면:

```bash
# 출력 yaml을 입력용으로 복사 (덮어쓰기 보호)
cp dist/home.entity-mapping.yaml dist/home.user-mapping.yaml

# user-mapping.yaml 편집 → 본인 entity_id 채우기

# 재변환
floor3d-toolkit convert myhome.sh3d \
  --output dist/ \
  --name home \
  --mapping dist/home.user-mapping.yaml
```

> 동일 path를 `--mapping` 으로 넘기더라도 자동 `.bak` 백업 생성됨. 입력/출력 분리가 가장 안전.

차이점: `convert` 모드는 텍스처가 없어 단색 PBR로 렌더됨. 텍스처 살아 있는 룩이 필요하면 `pack` 모드 권장.

---

## 8. redchupa-cards/floor3d-wrapper-card 와 조합

[`redchupa-cards`](https://github.com/redchupa/redchupa-cards)의 `floor3d-wrapper-card`는 floor3d-card 위에 시간대 자동 회전 UI를 얹어 줍니다. 같이 사용하면 잠금/카메라 프리셋 편의 기능을 더 누릴 수 있습니다.

---

## 9. 보안 / 프라이버시

이 toolkit이 만든 `.glb`/`.yaml`은 본인 가옥의 평면도 정보를 담고 있습니다. **공개 레포지토리에 절대 커밋하지 마세요.** `.gitignore`가 `*.sh3d`, `*.obj`, `*.mtl`, `*.glb`, `myhome*` 패턴을 기본 차단합니다.

이 toolkit은 본인 도면 데이터를 어디로도 전송하지 않으며, 모든 변환은 로컬에서만 일어납니다.
