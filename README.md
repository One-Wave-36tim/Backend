# Pro-Logue
### 커리어라는 본편이 시작되기 전, 나만의 프롤로그를 쓰다
**검증되지 않은 취준을 끝내는 AI 기반 실전 커리어 리플렉션 플랫폼**


<br>

## 🔍 프로젝트 소개

Pro-logue는 극심한 취업난 속에서  
“이 정도 준비로 괜찮은가?”, “내 경험은 실제로 통할까?”라는 질문에 답하지 못한 채  
불안한 준비를 반복하는 취준생의 현실에서 출발했습니다.

준비는 충분하다고 느끼지만,  
그 준비가 **실제로 검증된 적은 없는 상태**로 면접과 직무에 진입하는 구조적 문제에 주목합니다.

Pro-logue는 자소서를 대신 써주지 않는 **AI 기반 실전 검증 플랫폼**입니다.  
대신 사용자가 자신의 경험을 **검증 · 전략 · 실전**의 관점에서 반복적으로 점검하며,  
면접과 직무 현장에서 **스스로 말하고 판단할 수 있는 사람**이 되도록 돕습니다.


<br>

## 📌 주요 기능

* **경험 검증 리플렉션**  
  포트폴리오·노션·블로그·PDF를 기반으로 AI가 *답*이 아닌 *질문*을 던집니다.

* **전략형 유도 질문 생성**  
  Why / How / Conflict 질문을 통해 경험의 판단 근거와 선택 이유를 드러냅니다.

* **AI 모의 면접 (STT 기반)**  
  말의 속도, 침묵, 반복어 등 정량 지표로 실전 말하기 능력 피드백 제공.

* **직무 고통 시뮬레이션**  
  직무별 최악의 상황을 제시해 감정·판단·대응 전략을 검증합니다.


<br>

## 🛠 기술 구현

### 기술 스택

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


### 기능 구현 및 기술 포인트

#### 1️⃣ 포트폴리오 분석

사용자가 업로드한 포트폴리오 텍스트를 기반으로, FastAPI + SQLAlchemy로 저장된 데이터를 읽어 Gemini API 프롬프트를 구성하여 분석합니다.
분석 결과는 핵심 요약, 강점, 논리적 공백, 추가 질문 포인트 형태로 생성되며, 이후 질문 생성 단계에서 재활용할 수 있도록 DB에 저장됩니다.

#### 2️⃣ 전략형 유도 질문

포트폴리오 분석 결과와 사용자의 Q/A 히스토리를 결합해 프롬프트를 구성하고, Gemini API로부터 1회 1질문 형태의 응답을 받습니다.
질문은 대화 흐름을 반영해 꼬리질문이나 새로운 관점으로 확장되며, 사용자가 종료를 요청하면 종료 문구만 반환되도록 설계했습니다.

#### 3️⃣ 포트폴리오 업로드/관리

Notion, 블로그, PDF 등 다양한 소스 타입을 구분해 검증하고, 업로드된 정보를 Pydantic 모델로 관리합니다.
현재는 메모리 저장 방식으로 유지하며 조회, 목록, 삭제가 가능하도록 구성했으며, 향후 DB 저장으로 확장할 수 있는 인터페이스를 분리해두었습니다.

#### 4️⃣ 직무 시뮬레이션

직무와 공고 맥락을 기반으로 Gemini API를 호출해 “다급한 팀장 / 화난 고객 / 협력사” 등의 페르소나 대화를 생성합니다.
응답에 따라 논리성, 책임감, 멘탈, 협업 점수를 누적하며, 세션과 대화 로그는 SQLAlchemy로 저장됩니다.
마지막에는 대화 로그와 누적 점수를 기반으로 유형, 레이더 점수, 베스트/워스트 순간, 요약, 자소서 문구 형태의 리포트를 제공합니다.
