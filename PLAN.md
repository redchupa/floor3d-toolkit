# floor3d-toolkit — Sweet Home 3D → HA 3D 평면도 풀스택

## 1. 목적

> Sweet Home 3D로 그린 평면도를 **자동으로 HA floor3d-card 가능한 glb + 엔티티 매핑**으로 변환하는 CLI/패키지.

**왜?**
- `homeassistant_mcp/sweethome/`에 sh3d → obj → glb 파이프라인이 v6~v25까지 25버전 프로토타입 존재.
- transform 스크립트 8개, 가구 추출 스크립트, 머터리얼/포인트라이트 처리 코드 보유 — **80% 완성**.
- 한국 HA 커뮤니티에 3D 평면도 가이드 부재. floor3d-card 자체는 외산 카드이고 설정이 난해.
- `redchupa-cards`의 floor3d-wrapper-card와 페어 패키징 → 종합 솔루션.

## 2. 타겟 사용자

- floor3d-card를 시도했다가 좌절한 HA 사용자
- Sweet Home 3D로 도면 그릴 줄 아는 사용자 (한국 부동산 평면도 그려본 사람 많음)
- `redchupa-cards` 사용자 (floor3d-wrapper-card 같이 사용)

## 3. 범위

**IN (v1)**
- ✅ `.sh3d` → `.obj/.mtl` 변환 (가구·조명·머터리얼 포함)
- ✅ `.obj` → `.glb` (Three.js 호환) 변환
- ✅ 자동 normals 재계산 + 머터리얼 정리
- ✅ 가구 ↔ HA 엔티티 매핑 YAML 자동 생성 (이름 매칭 휴리스틱)
- ✅ 포인트라이트 자동 추출 (HA light.* 엔티티 후보)
- ✅ floor3d-card config YAML 생성기
- ✅ CLI: `floor3d-toolkit convert myhome.sh3d --output dist/`

**OUT (v1)**
- ❌ 카드 자체 (`redchupa-cards`가 wrapper 담당)
- ❌ 실시간 3D 편집기
- ❌ 다른 도면 도구 (AutoCAD, Revit 등) — Sweet Home 3D 한정

## 4. 아키텍처

```
Python CLI (Click 또는 Typer)
├── sh3d_parser/      Sweet Home 3D .sh3d (= zip) 파싱
├── obj_writer/       OBJ + MTL 작성
├── obj_to_glb/       trimesh 또는 pyassimp 기반
├── entity_mapper/    가구 이름 → HA 엔티티 휴리스틱 매핑
├── light_extractor/  포인트라이트 → HA light entity 후보
└── card_config_gen/  floor3d-card YAML 생성

의존성 (모두 무료/OSS):
- trimesh, pygltflib, lxml, pyyaml
- (선택) blender headless — glb 최적화용
```

데이터 흐름:
```
myhome.sh3d  ──parse──>  furniture list + walls + lights
                                  │
                            ┌─────┴─────┐
                            ▼           ▼
                       obj/mtl 생성   entity 매핑 YAML
                            │           │
                        normals 재계산    │
                            ▼           │
                        myhome.glb       │
                                         ▼
                              floor3d-card config YAML
```

## 5. 파일 구조 (v1 골격)

```
floor3d-toolkit/
├── README.md                  # 한·영 (kr_component_kit 톤)
├── LICENSE                    # MIT
├── PLAN.md
├── CLAUDE.md
├── .gitignore
├── pyproject.toml
├── floor3d_toolkit/
│   ├── __init__.py
│   ├── cli.py                # entry: `floor3d-toolkit convert ...`
│   ├── sh3d_parser.py
│   ├── obj_writer.py
│   ├── obj_to_glb.py
│   ├── entity_mapper.py
│   ├── light_extractor.py
│   └── card_config_gen.py
├── tests/
│   ├── fixtures/             # 합성 sh3d (실가옥 X)
│   │   └── sample_apartment.sh3d
│   └── test_*.py
├── examples/
│   ├── floor3d-card-config.yaml.example
│   └── entity-mapping.yaml.example
├── docs/
│   ├── tutorial-ko.md        # Sweet Home 3D 그리기 → 변환 → HA 적용
│   ├── tutorial-en.md
│   └── images/               # 모든 스크린샷 합성 도면 사용
└── .github/workflows/
    ├── test.yml              # pytest
    └── release.yml           # PyPI 배포 (선택, M3)
```

## 6. 마일스톤

### M0 — 자산 정리 (1 세션)
- [ ] `homeassistant_mcp/sweethome/` 25버전 스크립트 분석 → v25 최종 패턴 추출
- [ ] **모든 본인 도면(myhome.sh3d, 좌표 노출 obj/mtl) 레포에 가져오지 않음** — 합성 fixture만 생성
- [ ] pyproject.toml + 기본 CLI 스켈레톤
- [ ] tests/fixtures/sample_apartment.sh3d — 가짜 2bed 아파트 (합성)

### M1 — sh3d → glb 변환 (1~2 세션)
- [ ] sh3d_parser.py — .sh3d (zip) 안의 Home.xml 파싱
- [ ] obj_writer.py — `homeassistant_mcp/sweethome/sh3d_to_obj_final.py` 정리
- [ ] obj_to_glb.py — `homeassistant_mcp/sweethome/sh3d_to_glb.py` 정리
- [ ] rebuild_obj_with_normals 로직 통합 (`sweethome/rebuild_obj_with_normals.py`)
- [ ] CLI: `floor3d-toolkit convert input.sh3d` → output/*.glb

### M2 — 엔티티 매핑 + 카드 config (1~2 세션)
- [ ] entity_mapper.py — 휴리스틱 (예: "거실 천장등" → `light.living_room_main`)
- [ ] light_extractor.py — 포인트라이트 → HA light entity candidate
- [ ] card_config_gen.py — floor3d-card 호환 YAML 출력
- [ ] examples/*.yaml 모두 합성 데이터

### M3 — 문서·릴리스
- [ ] tutorial-ko.md — 합성 도면으로 처음부터 끝까지 가이드
- [ ] tutorial-en.md
- [ ] GitHub Actions release.yml (PyPI 배포)
- [ ] `redchupa-cards` README에서 본 패키지 링크
- [ ] 후원 섹션 (토스/PayPal)

## 7. 무료/보안 가드 (본 레포 특화)

### 본인 도면 절대 금지
- 본인 실가옥 도면(myhome.sh3d, myhome_v25.obj 등)은 **fixture로도 사용 금지**.
- 본인 평면도가 들어가면 → 가옥 구조 + 가구 배치 + 방 용도 노출.
- M0에서 별도 **합성 fixture (2bed 일반 아파트)** 를 새로 그릴 것.

### 가구 이름 매핑 휴리스틱
- 본인이 쓰는 한국 가구 이름 패턴(예: "안방 무드등")을 코드에 박지 말 것.
- 룰은 일반화하여 (예: "{room}_{type}" 매칭) 다른 사용자도 쓸 수 있게.

### CLI 출력
- 진단 로그에 절대 사용자 파일 경로 풀패스 출력 X (Windows 사용자명 노출 방지)
- relative path 또는 마스킹

### 문서 스크린샷
- Sweet Home 3D 캡처 이미지에 본인 실주소 노출 X
- "테스트 아파트 30평형" 같은 합성 라벨만

## 8. 본인 자산 참조 (재활용 가능 경로)

| 자산 | 위치 | 정리 방식 |
|---|---|---|
| sh3d → obj 최종버전 | `homeassistant_mcp/sweethome/sh3d_to_obj_final.py` | 로직만 추출, 파일 경로 하드코딩 제거 |
| obj → glb | `homeassistant_mcp/sweethome/sh3d_to_glb.py` | 동일 |
| normals 재계산 | `homeassistant_mcp/sweethome/rebuild_obj_with_normals.py` | 동일 |
| 머터리얼 정리 | `homeassistant_mcp/sweethome/fix_obj_materials.py` | 동일 |
| floor3d-card 설정 빌더 | `homeassistant_mcp/sweethome/build_floor3d_config.py` | 휴리스틱 일반화 |
| 가구 추출 | `homeassistant_mcp/sweethome/sh3d_furniture_extract.py` | 동일 |
| floor3d-card 라이브러리 | `homeassistant_mcp/sweethome/floor3d-card.js` | 참조만, 본 레포에 미포함 |
| 메모 | `homeassistant_mcp/memory/floor3d_card_debug.md` | 함정 정보 추출 |

> **재활용 워크플로**: 위 .py를 그대로 카피 X. 로직만 새 파일에 옮기되 (1) 파일 경로 인자화, (2) 본인 도면 가정 제거, (3) docstring·테스트 추가.

## 9. 수락 기준 (v1.0 DoD)

- [ ] CLI 한 줄로 `sample_apartment.sh3d` → `.glb` + entity-mapping.yaml + card-config.yaml 생성
- [ ] 생성된 glb를 floor3d-card에 로드, redchupa-cards/floor3d-wrapper-card에서 정상 렌더
- [ ] pytest 그린 (M1+M2 핵심 경로)
- [ ] README ko/en, tutorial ko/en
- [ ] PyPI 배포 (M3)
- [ ] 보안 grep: `192.168` / `redchupa` / 가족 실명 / 본인 동·호수 / 도로명 0건
- [ ] `homeassistant_mcp/sweethome/`의 본인 obj/mtl 파일 미포함 확인

## 10. 다음 세션 시작 프롬프트

```
이 폴더는 floor3d-toolkit 프로젝트입니다.
PLAN.md, CLAUDE.md, 그리고 ../MASTER_PLAN.md 를 먼저 읽으세요.

먼저 M0(자산 정리)부터:
1. ../homeassistant_mcp/sweethome/ 에 있는 sh3d 처리 스크립트 8개의 최종 버전 파악
2. 본인 도면(myhome.*)은 절대 가져오지 말고, tests/fixtures/sample_apartment.sh3d 합성 데이터 생성
3. pyproject.toml + floor3d_toolkit/cli.py 스켈레톤
4. tests/ 기본 구조

PLAN.md §7 (보안 가드) 와 MASTER_PLAN.md 공통 규칙 준수 — 특히 본인 가옥 평면도/주소/IP/실명 절대 포함 금지.
끝나면 진행사항 요약 + 다음 단계 제안.
```
