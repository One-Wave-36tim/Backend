# Pro-Logue
### 커리어라는 본편이 시작되기 전, 나만의 프롤로그를 쓰다
**검증되지 않은 취준을 끝내는 AI 기반 실전 커리어 리플렉션 플랫폼**

<br>

## 🔍 프로젝트 소개

Pro-Logue는  
"이 정도 준비로 괜찮은가?", "내 경험은 실제로 통할까?"라는 질문에 답하지 못한 채  
불안한 준비를 반복하는 취준생의 현실에서 출발했습니다.

LLM이 자소서를 대신 써주는 시대,  
겉으로는 그럴듯하지만 **정작 본인이 자기 경험을 설명하지 못하는 사람**이 늘어나고 있습니다.  
스스로에 대한 확신이 부족하고, 자기이해도가 낮은 채로 면접장에 서는 현실 —  
우리는 그 문제를 해결하고 싶었습니다.

그래서 '더 잘 쓰는 자소서'가 아니라  
**현장에서 직접 말할 수 있는 경험**을 만드는 데 집중합니다.  
사용자가 자신의 경험을 **검증 · 전략 · 실전** 관점에서 반복적으로 점검하며,  
면접과 직무 현장에서 **스스로 말하고 판단할 수 있는 사람**이 되도록 돕습니다.

<br>

## 📌 주요 기능

#### 1️⃣ 내 경험 돌아보기
포트폴리오, 노션, 블로그, PDF 등 내가 해온 일을 **AI가 질문으로 살펴보고 스스로 점검**하게 해줍니다.  
*예: “이 프로젝트에서 가장 어려웠던 부분은 뭐야?”, “왜 이런 방식을 선택했어?”*

#### 2️⃣ 선택 이유와 판단 점검
AI가 ‘왜 그렇게 했는지’, ‘어떻게 해결했는지’, ‘문제는 없었는지’ 같은 **핵심 질문을 하나씩 던져** 내 경험과 판단을 명확히 분석하게 합니다.  
> 그냥 답을 알려주는 게 아니라 **스스로 이유를 정리하게 하는 기능**입니다.

#### 3️⃣ 직무 상황 미리 체험하기
AI가 직무에서 벌어질 수 있는 **힘든 상황이나 갈등 상황**을 만들어, 내가 어떻게 대응할지 **실전처럼 연습**할 수 있습니다.  
*예: “팀장이 갑자기 마감일을 앞당겼을 때 어떻게 대응할래?”, “고객이 화가 났을 때 어떤 조치를 취할래?”*

<br>

## 🧰 개발 환경

- **Front**: Flutter, Dart
- **Back-end**: Python, FastAPI, SQLAlchemy
- **DB/Infra**: PostgreSQL, Supabase
- **AI**: Gemini API
- **버전 및 이슈관리**: GitHub
- **협업 툴**: Notion, Discord

<br>

## 🛠 기술 스택

#### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-333333?style=for-the-badge&logo=uvicorn&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
#### Frontend
![Flutter](https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white)
![Dart](https://img.shields.io/badge/Dart-0175C2?style=for-the-badge&logo=dart&logoColor=white)


<br>

## 📂 프로젝트 구조

```
app/
  main.py
  router.py
  controllers/
  services/
  schemas/
  db/
    entities/
    repositories/
  core/
tests/
assets/
```

<br>

<br>

## ✨ 기능 구현 및 기술 포인트

### 1️⃣ 포트폴리오 분석
사용자가 업로드한 포트폴리오 텍스트를 기반으로, FastAPI + SQLAlchemy로 저장된 데이터를 읽어 Gemini API 프롬프트를 구성합니다.  
분석 결과는 핵심 요약, 강점, 논리적 공백, 추가 질문 포인트 형태로 생성되며, 이후 질문 생성 단계에서 재활용할 수 있도록 DB에 저장됩니다.

### 2️⃣ 전략형 유도 질문
포트폴리오 분석 결과와 사용자의 Q/A 히스토리를 결합해 프롬프트를 구성하고, Gemini API로부터 1회 1질문 형태의 응답을 받습니다.  
질문은 대화 흐름을 반영해 꼬리질문이나 새로운 관점으로 확장되며, 사용자가 종료를 요청하면 종료 문구만 반환되도록 설계했습니다.  
자기회귀적 질문 흐름을 통해 사용자가 스스로 답을 찾아가도록 유도하며, 이전 답변의 맥락을 기반으로 깊이 있는 다음 질문을 생성합니다.

### 3️⃣ 포트폴리오 업로드/관리
Notion, 블로그, PDF 등 다양한 소스 타입을 구분해 검증하고, 업로드된 정보를 Pydantic 모델로 관리합니다.  
업로드된 포트폴리오는 SQLAlchemy 기반 DB 저장으로 유지되며, 조회·목록·삭제까지 일관된 흐름으로 처리됩니다.

### 4️⃣ 직무 시뮬레이션
직무와 공고 맥락을 기반으로 Gemini API를 호출해 “다급한 팀장 / 화난 고객 / 협력사” 등의 페르소나 대화를 생성합니다.  
응답에 따라 논리성, 책임감, 멘탈, 협업 점수를 누적하며, 세션과 대화 로그는 SQLAlchemy로 저장됩니다.  
마지막에는 대화 로그와 누적 점수를 기반으로 유형, 레이더 점수, 베스트/워스트 순간, 요약, 자소서 문구 형태의 리포트를 제공합니다.

<br>

## 🔧 트러블슈팅 & 기술적 의사결정

### 1️⃣ 프롬프트 설계: 사용자의 깊은 자기이해를 이끌어내는 방법

**문제 상황**  
사용자가 자신의 프로젝트에 대해 얼마나 깊이 이해하고 있는지를 질문으로 파악하는 프롬프트 설계가 가장 어려웠습니다.  
단순히 정보를 묻는 질문이 아니라, 사용자가 스스로 **생각의 구조를 점검하고 경험을 정리**할 수 있는 질문을 만들어야 했습니다.

**해결 전략**  
소크라테스식 귀납적 추론에서 영감을 받아, **자기회귀적(Auto-regressive) 질문 흐름**을 설계했습니다.
- 이전 답변의 맥락을 기반으로 다음 질문을 생성하는 방식
- "왜?", "어떻게?", "그래서?"로 이어지는 **전략적 유도 질문** 구조
- Gemini API에 히스토리 기반 프롬프트를 전달해 맥락을 유지하면서도 깊이 있는 질문을 생성
- 단순 정보 수집이 아닌, **사용자가 스스로 답을 찾아가도록 유도**하는 대화 흐름 구현

**기술 구현**
```python
# 이전 대화 히스토리 + 포트폴리오 분석 결과를 결합한 프롬프트 구성
# 사용자 답변 패턴을 분석해 다음 질문의 방향성 결정
# "종료" 의도 감지 시 자연스러운 마무리 멘트 생성
```

---

### 2️⃣ 기술 스택 선택: 웹 vs 플러터

**아쉬운 결정**  
웹으로 개발했다면 훨씬 편리하고 좋은 UI/UX를 구현할 수 있었을 것입니다.  
반응형 디자인, 풍부한 라이브러리, 빠른 프로토타이핑 등 웹의 장점이 명확했습니다.

**현실적 선택**  
- 팀 내에 웹 프론트엔드 스택을 보유한 인원이 없었습니다
- **"개발을 못하는 것보다 완성도 있는 앱을 만드는 것"**이 더 중요하다고 판단
- Flutter를 선택해 크로스플랫폼 앱으로 완성도를 높이는 방향으로 진행

**결과**  
Flutter로 네이티브에 가까운 경험을 제공했지만, 웹의 유연함과 접근성 측면에서는 여전히 아쉬움이 남습니다.  
향후 웹 버전 출시를 통해 더 많은 사용자에게 접근할 계획입니다.

---

### 3️⃣ 기획 방향: 얼어붙은 시장과 개인의 자기이해

**문제 인식**  
취업 시장 자체가 얼어붙은 상황을 근본적으로 해결하고 싶었습니다.  
하지만 현실적으로 **거시적 시장 문제를 직접 해결하기는 어렵다는 한계**가 명확했습니다.

**해결 방향 전환**  
시장을 바꾸는 대신, **사용자 개개인의 탄탄한 자기이해**를 문제 해결의 실마리로 삼았습니다.
- 취준생이 자신의 경험을 명확히 이해하고 말할 수 있다면
- 불확실한 시장에서도 **자신만의 경쟁력**을 만들 수 있다는 믿음
- "검증되지 않은 준비"에서 벗어나 **실전에서 통하는 경험**으로 전환하도록 지원

**Pro-Logue의 핵심 가치**  
> "시장을 바꿀 수 없다면, 시장에서 살아남을 수 있는 개인을 만든다"

---

### 4️⃣ 포트폴리오 분석 API 안정성

**발생한 문제**  
- 분석 결과가 없을 때 질문 생성이 실패하는 이슈
- 스키마와 엔티티 간 필드 불일치로 인한 접근 오류

**해결 방법**
- 분석 결과 존재 여부를 먼저 확인하고, 없으면 안내 메시지 반환하도록 예외 처리
- 응답 스키마에서 불필요한 필드 제거 후 Pydantic 모델과 SQLAlchemy 엔티티 간 일관성 유지
- 데이터 검증 로직을 서비스 레이어에 추가해 런타임 오류 방지

---

### 5️⃣ 직무 시뮬레이션 세션 관리

**발생한 문제**  
세션 로그 누적 중 사용자/AI 턴 순서가 꼬여서 대화 흐름이 깨지는 현상 발생

**해결 방법**
- `turn_order`를 DB에서 최대값 기준으로 계산해 자동 증가 처리
- 각 턴마다 명확한 역할(user/assistant) 구분으로 순서 보장
- SQLAlchemy의 트랜잭션 격리 수준을 조정해 동시성 이슈 방지

```python
# turn_order = max(existing_turns) + 1
# role 명시: "user" | "assistant"
# 트랜잭션 커밋 전 순서 검증
```

---

### 6️⃣ Gemini API 응답 안정성

**발생한 문제**  
- API 응답 지연으로 인한 타임아웃
- 예상치 못한 응답 형식으로 인한 파싱 오류

**해결 방법**
- 타임아웃 설정 및 재시도 로직 추가 (exponential backoff)
- 응답 검증 레이어를 두어 예외 응답 필터링
- 스트리밍 응답 대신 단일 응답 방식으로 안정성 확보

---

## 📸 화면 미리보기

<table>
  <tr>
    <td align="center"><img src="image/메인화면.png" width="320" /><br/>메인화면</td>
    <td align="center"><img src="image/마이페이지.png" width="320" /><br/>마이페이지</td>
  </tr>
  <tr>
    <td align="center"><img src="image/프로젝트%20심층%20인터뷰.png" width="320" /><br/>프로젝트 심층 인터뷰</td>
    <td align="center"><img src="image/자소서%20작성.png" width="320" /><br/>자소서 작성</td>
  </tr>
  <tr>
    <td align="center"><img src="image/직무시뮬레이션%20챗봇.png" width="320" /><br/>직무 시뮬레이션 챗봇</td>
    <td align="center"><img src="image/직무%20시뮬레이션%20결과.png" width="320" /><br/>직무 시뮬레이션 결과</td>
  </tr>
  <tr>
    <td align="center"><img src="image/모의%20면접%20진행.png" width="320" /><br/>모의 면접 진행</td>
    <td align="center"><img src="image/모의면접%20결과.png" width="320" /><br/>모의 면접 결과</td>
  </tr>
  <tr>
    <td align="center"><img src="image/최종피드백%20결과.png" width="320" /><br/>최종 피드백 결과</td>
    <td></td>
  </tr>
</table>

<br>

## 🙋🏻‍♀️ Members

<table>
  <tbody>
    <tr>
      <td align="center">
        <a href="https://github.com/mimo626">
          <img src="https://avatars.githubusercontent.com/mimo626" width="100px;" alt="강민주"/>
          <br /><sub><b>강민주</b></sub>
        </a>
      </td>
      <td align="center">
        <a href="https://github.com/zzmnxn">
          <img src="https://avatars.githubusercontent.com/zzmnxn" width="100px;" alt="박지민"/>
          <br /><sub><b>박지민</b></sub>
        </a>
      </td>
      <td align="center">
        <a href="https://github.com/knox-glorang">
          <img src="https://avatars.githubusercontent.com/knox-glorang" width="100px;" alt="홍기현"/>
          <br /><sub><b>홍기현</b></sub>
        </a>
      </td>
      <td align="center">
        <a href="https://github.com/yerriiniii">
          <img src="https://avatars.githubusercontent.com/yerriiniii" width="100px;" alt="박예린"/>
          <br /><sub><b>박예린</b></sub>
        </a>
      </td>
    </tr>
  </tbody>
</table>
