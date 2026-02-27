# 제안서검색봇 Slack App 생성 가이드

> 이 문서는 Slack Workspace 관리자가 **제안서 시맨틱 검색 봇**을 설정하기 위한 단계별 가이드입니다.
> 설정 완료 후 3개 토큰을 개발팀에 전달해주세요.

---

## 사전 요구사항

- Slack Workspace **관리자 권한** (또는 앱 설치 권한)
- 브라우저에서 https://api.slack.com/apps 접속 가능

---

## Step 1. 앱 생성

1. https://api.slack.com/apps 접속
2. 우측 상단 **[Create New App]** 클릭
3. **From scratch** 선택
4. 아래 정보 입력:
   - **App Name**: `제안서검색봇`
   - **Pick a workspace**: 사용할 워크스페이스 선택
5. **[Create App]** 클릭

---

## Step 2. Socket Mode 활성화 + App-Level Token 생성

Socket Mode는 봇이 별도 서버(공인 IP) 없이 Slack과 통신할 수 있게 해주는 방식입니다.

1. 좌측 메뉴에서 **Settings** > **Socket Mode** 클릭
2. **Enable Socket Mode** 토글을 **On**으로 변경
3. 토글을 켜면 **App-Level Token 생성 다이얼로그**가 자동으로 나타남
   - (다이얼로그가 안 뜨면: 좌측 **Settings** > **Basic Information** > 하단 **App-Level Tokens** 섹션에서 **[Generate Token and Scopes]** 클릭)
4. 다이얼로그에서:
   - **Token Name**: `socket-token` (아무 이름이나 가능)
   - **[Add Scope]** 클릭 → `connections:write` 선택
   - **[Generate]** 클릭
5. 생성된 토큰 (`xapp-1-...` 형식) 복사하여 안전한 곳에 저장

> **이것이 `SLACK_APP_TOKEN` 입니다** (전달 항목 1/3)

---

## Step 3. Bot Token Scopes 설정

봇이 메시지를 보내고, 멘션을 읽고, 사용자 정보를 조회할 수 있도록 권한을 부여합니다.

1. 좌측 메뉴 **Features** > **OAuth & Permissions** 클릭
2. 아래로 스크롤하여 **Scopes** > **Bot Token Scopes** 섹션 찾기
3. **[Add an OAuth Scope]** 버튼으로 아래 6개 스코프 추가:

| Scope | 용도 |
|-------|------|
| `chat:write` | 봇이 채널에 메시지를 보냄 |
| `commands` | 슬래시 커맨드(`/proposal-search`) 사용 |
| `app_mentions:read` | `@제안서검색봇` 멘션을 감지 |
| `users:read` | 검색 요청자의 이름을 조회 |
| `im:history` | DM(1:1 대화) 메시지를 읽음 |
| `im:write` | DM으로 검색 결과를 응답 |

---

## Step 4. Slash Command 등록

사용자가 `/proposal-search` 명령어로 검색할 수 있도록 등록합니다.

1. 좌측 메뉴 **Features** > **Slash Commands** 클릭
2. **[Create New Command]** 클릭
3. 아래 정보 입력:

| 항목 | 값 |
|------|-----|
| **Command** | `/proposal-search` |
| **Short Description** | `제안서 시맨틱 검색` |
| **Usage Hint** | `[검색어] 예: AWS 금융 프로젝트` |

4. **[Save]** 클릭

> Request URL은 Socket Mode에서는 자동 처리되므로 비워두어도 됩니다.

---

## Step 5. Event Subscriptions 활성화

봇이 `@멘션`과 DM 메시지를 수신할 수 있도록 이벤트를 구독합니다.

1. 좌측 메뉴 **Features** > **Event Subscriptions** 클릭
2. **Enable Events** 토글을 **On**으로 변경
3. 아래로 스크롤하여 **Subscribe to bot events** 섹션 찾기
4. **[Add Bot User Event]** 버튼으로 아래 2개 이벤트 추가:

| Event | 용도 |
|-------|------|
| `app_mention` | 채널에서 `@제안서검색봇 검색어` 감지 |
| `message.im` | DM으로 보낸 검색어 감지 |

5. 하단 **[Save Changes]** 클릭

---

## Step 6. App Home 설정 (선택사항)

DM 탭에서 봇과 대화하려면 Messages 탭을 활성화해야 합니다.

1. 좌측 메뉴 **Features** > **App Home** 클릭
2. **Show Tabs** 섹션에서:
   - **Messages Tab** 체크 → **On**
   - "Allow users to send Slash commands and messages from the messages tab" 체크

---

## Step 7. Workspace에 설치 + 토큰 수집

1. 좌측 메뉴 **Settings** > **Install App** 클릭
2. **[Install to Workspace]** (또는 **[Reinstall to Workspace]**) 클릭
3. 권한 승인 화면에서 **[허용]** 클릭
4. 설치 완료 후 표시되는 **Bot User OAuth Token** (`xoxb-...` 형식) 복사

> **이것이 `SLACK_BOT_TOKEN` 입니다** (전달 항목 2/3)

5. 좌측 메뉴 **Settings** > **Basic Information** 클릭
6. 아래로 스크롤하여 **App Credentials** 섹션 찾기
7. **Signing Secret** 옆의 **[Show]** 클릭 후 복사

> **이것이 `SLACK_SIGNING_SECRET` 입니다** (전달 항목 3/3)

---

## Step 8. 봇을 채널에 초대

봇이 특정 채널에서 멘션에 응답하려면 해당 채널에 초대해야 합니다.

1. Slack에서 봇을 사용할 채널로 이동
2. 메시지 입력창에 `/invite @제안서검색봇` 입력 후 전송
3. 또는 채널 설정 > **멤버** > **멤버 추가** 에서 `제안서검색봇` 검색하여 추가

---

## 개발팀에 전달할 토큰 (총 3개)

| 환경변수 | 형식 | 어디서 확인 |
|----------|------|-------------|
| `SLACK_APP_TOKEN` | `xapp-1-...` | Step 2에서 생성한 App-Level Token |
| `SLACK_BOT_TOKEN` | `xoxb-...` | Step 7의 Bot User OAuth Token |
| `SLACK_SIGNING_SECRET` | 영숫자 32자리 | Step 7의 Basic Information > Signing Secret |

> 토큰은 민감 정보입니다. Slack DM이나 사내 보안 채널을 통해 전달해주세요.

---

## 봇 사용 방법 (설치 완료 후)

| 방법 | 예시 |
|------|------|
| 슬래시 커맨드 | `/proposal-search AWS 기반 금융 프로젝트` |
| 채널 멘션 | `@제안서검색봇 쿠버네티스 마이그레이션 사례` |
| DM | 봇에게 직접 `공공기관 클라우드 전환` 입력 |

---

## 문제 해결

| 증상 | 원인 및 해결 |
|------|-------------|
| 봇이 응답하지 않음 | `python main.py` 가 실행 중인지 확인 |
| `not_in_channel` 에러 | Step 8의 채널 초대 필요 |
| `missing_scope` 에러 | Step 3의 Bot Token Scopes 누락 → 추가 후 **Reinstall** |
| `invalid_auth` 에러 | 토큰이 올바른지 확인 (xoxb/xapp 형식) |
| 슬래시 커맨드가 안 보임 | Step 4 등록 후 **Reinstall to Workspace** 필요 |
| DM이 안 됨 | Step 6의 App Home > Messages Tab 활성화 확인 |
