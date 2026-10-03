# 🏢 NextAI - Jev형 판단 AI 기반 1인 기업 3D 물리 오피스 시뮬레이터

> **"AI는 독단적으로 결정하지 않고 판단(Sensor)만 수행하며, 의사결정(Decision)은 인간의 규칙 체인과 대표(CEO)가 통제합니다."**

NextAI는 1인 에듀테크 기업가의 이메일/문의 처리 워크플로우를 **Jev 스타일의 System 1 판단형 AI(Sensor)** 와 **System 2 결정 트리(Decision Tree)** 로 이원화하여 구현한 실시간 3D 물리 시뮬레이션 웹 애플리케이션입니다.

---

## ✨ 핵심 아키텍처 및 철학

```
[고객 문의 유입]
       │
       ▼
[System 1: Jev형 판단 AI (Sensor)]
  - 모델: tev1:0.8b (권장), tev1, jev (API키 필요), laya, nimble
  - 역할: 의사결정을 내리지 않고, 오직 상태 분석 / 카테고리 확률 / 신뢰도(confidence)만 산출
       │
       ▼
[System 2: 규칙 기반 의사결정 트리 (Decision Tree)]
  - 임계값 검증: confidence ≥ 0.70 이면 자율 부서 처리 / 미만이면 대표(CEO) 이관
  - 분기 집행: 환불 심사, 기술 지원, B2B 제휴, 수강 멘토링
       │
       ▼
[3D 리얼타임 물리 오피스 집행 (Three.js + Cannon.js)]
  - 우편물 3D 포물선 투사 및 물리 충돌 반응
  - 담당 부서 캐릭터 활성화 및 업무 초안 자동 생성
```

### 1. Jev형 판단 AI 라인업 (System 1)
* **`tev1:0.8b (권장)`**: 로컬 구동 초고속 System 1 판단 특화 SLM
* **`tev1 (풀버전)`**: 로컬 정밀 판단 모델
* **`jev (🔑 API 키 필요)`**: 고성능 클라우드 엔터프라이즈 판단 AI (`Authorization: Bearer <KEY>`, `x-api-key` 헤더 지원)
* **`laya`**: 도메인 특화 판단 모델
* **`nimble`**: 경량화 엣지 런타임 모델

### 2. 브라우저 설정 영구 유지 (LocalStorage Persistence)
사용자가 설정한 모든 환경이 브라우저 로컬 저장소에 안전하게 유지되며, 새로고침 후에도 그대로 복원됩니다:
* **선택한 AI 모델** (`tev1:0.8b`, `jev`, `laya` 등)
* **엔진 실행 모드** (로컬 실시간 연동 ↔ 체험 모드)
* **Jev API 인증 키 및 엔드포인트 URL**
* **효과음 ON / OFF**
* **시뮬레이션 배속 설정** (1x, 2x, 4x)
* **의사결정 트리 룰셋 & 임계값** (가중치 및 기준값 커스텀)
* **작업 이력 및 처리 통계 로그**

### 3. 사실적인 3D 인터랙티브 물리 엔진
* **Three.js & Cannon.js** 기반 실시간 물리 시뮬레이션
* 이메일 발송 시 물리 우편물 객체가 책상 위로 포물선을 그리며 투하
* 3D 사무실 책상 클릭 시 담당 부서 상세 정보 및 처리 템플릿 모달 팝업
* 2D 오리지널 레트로 픽셀 버전(`index_original.html`)과 실시간 전환 지원

---

## 🚀 빠른 시작 가이드

### 1. 웹 서버 실행
정적 웹 서버(포트 8888)를 실행합니다:

```bash
# 프로젝트 디렉터리에서 실행
python3 -m http.server 8888
```

브라우저에서 **[http://localhost:8888](http://localhost:8888)** 로 접속합니다.

### 2. 로컬 판단 AI 엔진(Ollama) 연동 (선택 사항)
로컬에서 실시간 SLM 추론을 연동하려면 브라우저 CORS 허용 옵션을 켜고 실행합니다:

```bash
# 터미널에서 실행
OLLAMA_ORIGINS="*" ollama serve
```

* 로컬 모델이 없거나 Ollama가 꺼져 있는 경우, 상단 뱃지를 클릭하여 **`체험 모드(Demo Mode)`** 로 즉시 전환하여 100% 동일한 3D 시뮬레이션을 즐기실 수 있습니다.

### 3. Jev 클라우드 모델 사용 시
1. 상단 내비게이션 바에서 **`🔑 Jev API 키`** 버튼을 클릭합니다.
2. 발급받으신 **Jev API Key**를 입력하고 저장합니다.
3. 모델 선택 드롭다운에서 **`jev (🔑 API 키 필요)`** 를 선택하면 실시간 클라우드 판단 엔진과 통신합니다.

---

## 📂 파일 구조

```
├── index.html           # 메인 3D 물리 시뮬레이션 & Jev 판단 웹 애플리케이션
├── index_3d.html        # 3D 버전 백업 및 동기화 파일
├── index_original.html  # 레트로 2D 픽셀 원본 보관 버전
├── .gitignore           # Git 제외 규칙
└── README.md            # 프로젝트 문서
```

---

## 🛠️ 기술 스택
* **Frontend**: HTML5, Vanilla JavaScript, Modern CSS3 (Glassmorphism & Cyberpunk Theme)
* **3D Graphics & Physics**: Three.js (r128), Cannon.js
* **AI Judgment Protocol**: Jev System One Sensor Specification (`POST /v1/systemone` & Structured JSON Chat Inference)
* **Audio**: Web Audio API (합성 레트로 사운드 엔진)
