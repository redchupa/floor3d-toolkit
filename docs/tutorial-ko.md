# 튜토리얼 — Sweet Home 3D 도면을 Home Assistant 3D 평면도로

> 처음부터 끝까지: Sweet Home 3D로 아파트 도면 그리기 → `floor3d-toolkit`으로 변환 → HA `floor3d-card`에 띄우기.

소요 시간: 도면 그리기 1~2시간 (한 번만), 변환·설정 10분.

## 0. 준비물

| | |
|---|---|
| Sweet Home 3D | 무료 GPL OSS, http://www.sweethome3d.com/ |
| Python | 3.11+ |
| Home Assistant | floor3d-card 설치 (HACS) |

## 1. 도면 그리기 (Sweet Home 3D)

1. Sweet Home 3D 실행, 새 프로젝트
2. 벽 그리기 — 실제 도면 치수대로
3. 가구 배치 — 기본 카탈로그의 stock 모델 사용 권장
4. **조명 배치가 가장 중요** — 각 방·구역마다 `Lights` 카테고리에서 천장 조명 하나씩 배치
5. 조명 이름을 알아보기 쉽게 변경 (예: "Living Room Main", "Kitchen Pendant")
6. `myhome.sh3d`로 저장

### 조명 이름 짓는 팁

`floor3d-toolkit`은 조명 이름을 그대로 ASCII 슬러그로 변환해서 mesh 노드 이름으로 사용합니다.

| Sweet Home 3D 조명 이름 | 자동 생성된 mesh node | 추천 HA 엔티티 |
|---|---|---|
| `Living Main Light` | `light_living_main_light` | `light.living_room_main` |
| `안방 조명` | `light_anbang_jomyeong` | `light.master_bedroom` |
| `Kitchen LED` | `light_kitchen_led` | `light.kitchen_led` |

이름을 명확히 지을수록 다음 단계의 매핑이 쉬워집니다.

## 2. 설치

```bash
pip install floor3d-toolkit
```

또는 개발용:
```bash
git clone https://github.com/redchupa/floor3d-toolkit
cd floor3d-toolkit
pip install -e ".[dev]"
```

## 3. 변환

```bash
floor3d-toolkit convert myhome.sh3d --output dist/ --name home
```

생성되는 파일:

```
dist/
├── home.obj                       # OBJ + MTL (디버깅·외부 툴용)
├── home.mtl
├── home.glb                       # floor3d-card가 읽는 파일
├── home.entity-mapping.yaml       # 수정 대상! (다음 단계)
└── home.card-config.yaml          # Lovelace에 붙여넣는 카드 설정
```

`floor3d-toolkit inspect myhome.sh3d` 로 벽·가구·조명 카운트 미리 보기도 가능합니다.

### 옵션

| 옵션 | 설명 |
|---|---|
| `--output / -o` | 출력 디렉터리 (기본 `dist/`) |
| `--name / -n` | 산출물 베이스 이름 (기본: 입력 파일명) |
| `--glb-url` | HA가 `.glb`를 서빙할 URL (기본 `/local/floor3d/home.glb`) |
| `--mapping` | 사용자 매핑 YAML (4단계에서 사용) |
| `--skip-furniture-meshes` | 가구를 박스로만 — 속도/용량 우선 |

## 4. 엔티티 매핑 편집

`home.entity-mapping.yaml`을 열면 각 mesh 노드별로 휴리스틱 추측이 들어 있습니다:

```yaml
# floor3d-toolkit entity mapping
entities:
  light_living_main_light: light.living_main_light  # confidence 0.6 (light_ prefix)
  light_kitchen_led: light.kitchen_led              # confidence 0.6 (light_ prefix)
  furn_refrigerator: switch.refrigerator             # confidence 0.6 (keyword 'refrigerator')
  furn_sofa: null                                    # confidence 0.0 — fill me in
  door_front: null                                   # confidence 0.4 (door_/window_ prefix)
```

각 행의 오른쪽을 실제 HA `entity_id`로 바꾸세요. 매핑하고 싶지 않은 가구는 `null` 유지 → 카드 config에서 제외됩니다.

## 5. 매핑 반영 후 재변환

```bash
floor3d-toolkit convert myhome.sh3d \
  --output dist/ \
  --name home \
  --mapping dist/home.entity-mapping.yaml
```

이제 `dist/home.card-config.yaml` 에 사용자가 지정한 엔티티 ID가 박힙니다.

## 6. Home Assistant 배포

### 6-1. glb 업로드

`.glb` 파일을 HA `/config/www/floor3d/` 디렉터리에 복사:

```
/config/www/floor3d/home.glb
```

(Samba / 파일 에디터 / SSH 등 편한 방법 사용)

### 6-2. floor3d-card 설치 (HACS)

HACS → Frontend → `floor3d-card` 검색·설치.

### 6-3. Lovelace에 카드 추가

`dist/home.card-config.yaml` 내용을 그대로 Lovelace 카드 YAML에 붙여넣기. `path:`/`objfile:` 이 `/local/floor3d/home.glb`를 가리키는지 확인.

새로고침하면 3D 평면도가 뜨고, on/off 시 매핑된 조명의 색이 바뀝니다.

## 7. 잘 안 될 때

| 증상 | 원인 / 해결 |
|---|---|
| glb는 떴는데 조명 클릭이 안 됨 | `home.entity-mapping.yaml`의 entity_id 가 실제 HA에 존재하는지 |
| 가구가 검은색 큐브로만 보임 | `--skip-furniture-meshes` 안 썼는지, sh3d 안의 모델 추출 실패 — 콘솔의 `parsed:` 라인의 furniture 카운트 확인 |
| 조명이 위치는 맞는데 천장 위로 너무 가까움 | `scene_builder.LIGHT_ELEVATION_FACTOR` (현재 0.93) 조정 가능 — 본인 도면의 천장 높이에 따라 |
| Sweet Home 3D 가구를 추가했는데 기존 매핑이 깨짐 | 같은 이름 추가 시 `_1`, `_2` 접미사가 붙음. 이름을 다르게 지으세요. |

## 8. redchupa-cards/floor3d-wrapper-card 와 조합

`redchupa-cards`의 `floor3d-wrapper-card`는 floor3d-card 위에 입력 모드/시간대 자동 회전 UI를 얹어 줍니다. 같이 사용하면 잠금/카메라 프리셋 같은 편의 기능을 그대로 누릴 수 있습니다.

자세한 사용법: https://github.com/redchupa/redchupa-cards

## 9. 보안 / 프라이버시

이 툴킷이 만든 `.glb`/`.yaml`은 본인 가옥의 평면도 정보를 담고 있습니다. **공개 레포지토리에 절대 커밋하지 마세요.**

이 패키지 자체는 본인 도면 데이터를 어디로도 전송하지 않으며, 모든 변환은 로컬에서만 일어납니다.
